"""SPEC 007 · QA integral synthetic dataset — constructores (`QA-DEMO-V1`).

Toda entidad creada aquí es **sintética, trazable, idempotente, removible y aislada**:

    prefijo        `QA-` en códigos de maestros, lotes, documentos SAP · `QA ` en nombres
    usuarios       `qa.*` con correo `@qa.globalavicola.com`
    marcador       `QA_DEMO_V1` en `extra_data`/`observations` de eventos, `source_system` de lotes,
                   `tax_id` de las empresas, `extra_data.marker` de referencias SAP
    SAP            `source_system = QA_SYNTHETIC`, jamás `SAP_HANA_CLOUD`/real

Los eventos operativos nacen por `OperationsService.create_event` (todos los validadores de
negocio se aplican) con `idempotency_key` determinista: volver a ejecutar no duplica. Las
transiciones de workflow usan los servicios reales (revisión, aprobación, corrección, reverso).
La historia aprobada en bloque usa `QA_HISTORY_FASTPATH` (estado + `ApprovalAction` + auditoría)
documentado en la SPEC; nunca salta validadores de alta.
"""
from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.cutover.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.notifications.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.audit.context import set_current_audit_user
from app.audit.helpers import audit_state_transition
from app.auth.models import Role, User
from app.auth.security import hash_password
from app.business_units.models import BusinessUnit, CompanyBusinessUnit, UserBusinessUnit
from app.integrations.sap.inbound.models import (JOB_COMPLETED, M_MAPPED, M_PENDING_MAPPING, P_PROMOTED,
                                                 P_STAGED_ONLY, V_INVALID, V_VALID, SapEntityMapping,
                                                 SapInboundRecord, SapInboundSyncJob)
from app.integrations.sap.inbound.promotion import upsert_reference
from app.integrations.sap.inbound.registry import HanaObject, get_definition
from app.integrations.sap.inbound.staging import canonical_hash, source_key, stage
from app.integrations.sap.models import SapReference, SapReferenceType
from app.lots.models import OpeningBalance
from app.masters.models import (Area, BirdTypeEnum, Breed, Company, CorrectionType, CullCause, Farm, FarmType,
                                FeedType, GeneticLine, GeneticWeightCurve, GeneticWeightCurvePoint, Hatcher,
                                Hatchery, House, HouseType, Incubator, Lot, LotStatus, Medication, MortalityCause,
                                ProcessingPlant, ProductivePhase, RejectionReason, SexEnum, Supplier, Transport,
                                Vaccine)
from app.notifications.models import Notification
from app.operations import schemas as op_schemas
from app.operations.models import EventStatus, OperationalEvent
from app.review import models as review_models

VERSION = "QA-DEMO-V1"
MARKER = "QA_DEMO_V1"
PREFIX = "QA-"
USER_PREFIX = "qa."
EMAIL_DOMAIN = "qa.globalavicola.com"  # dominio válido para EmailStr (F3/GA-FE-02-B: nada de .local/.test)
SAP_SOURCE = "QA_SYNTHETIC"
SAP_CLIENT = "100"

COMPANY_MAIN = "QA Avícola Integral C.A."
COMPANY_ISO = "QA Avícola Aislamiento C.A."
TAX_MAIN = f"{VERSION}-INTEGRAL"
TAX_ISO = f"{VERSION}-AISLAMIENTO"
ALL_BU = ("grandparent", "breeder", "hatchery", "broiler")

#: Roles canónicos (no se alteran). `Operador` del mandato ⇒ `Operador de Granja` (único rol operador).
ROL_ADMIN, ROL_SUP, ROL_APR, ROL_OP, ROL_SAP, ROL_AUD = (
    "Super Administrador", "Supervisor Avícola", "Aprobador", "Operador de Granja", "Analista SAP", "Auditor")

#: username, rol, empresa (MAIN|ISO), unidades concedidas, view_type, nombre, apellido, propósito
USUARIOS = (
    ("qa.admin", ROL_ADMIN, "MAIN", ALL_BU, "web", "QA", "Administrador", "configuración, maestros, usuarios, diagnóstico"),
    ("qa.supervisor", ROL_SUP, "MAIN", ALL_BU, "web", "QA", "Supervisora", "revisión, correcciones, reversos, cargas iniciales"),
    ("qa.approver", ROL_APR, "MAIN", ALL_BU, "web", "QA", "Aprobador", "aprobación y rechazo"),
    ("qa.operator.gp", ROL_OP, "MAIN", ("grandparent",), "web", "QA", "Operador GP", "registro operativo Progenitoras"),
    ("qa.operator.breeder", ROL_OP, "MAIN", ("breeder",), "web", "QA", "Operador Reproductoras", "registro operativo Reproductoras"),
    ("qa.operator.hatchery", ROL_OP, "MAIN", ("hatchery",), "web", "QA", "Operador Incubadora", "registro operativo Incubadora"),
    ("qa.operator.broiler", ROL_OP, "MAIN", ("broiler",), "web", "QA", "Operador Engorde", "registro operativo Engorde"),
    ("qa.sap", ROL_SAP, "MAIN", ALL_BU, "web", "QA", "Analista SAP", "Integración SAP (datos sintéticos)"),
    ("qa.auditor", ROL_AUD, "MAIN", ALL_BU, "web", "QA", "Auditora", "auditoría y reportes"),
    ("qa.mobile", ROL_OP, "MAIN", ("broiler",), "mobile", "QA", "Operador Móvil", "registro de campo en móvil"),
    ("qa.isolation", ROL_SUP, "ISO", ("breeder", "broiler"), "web", "QA", "Aislamiento", "multiempresa y BU apagadas"),
    ("qa.isolation.operator", ROL_OP, "ISO", ("breeder", "broiler"), "web", "QA", "Operador Aislamiento", "registro en la empresa 2"),
)


def hoy() -> date:
    return date.today()


def D(n: int) -> date:
    return hoy() - timedelta(days=n)


def DT(n: int) -> datetime:
    return datetime.combine(D(n), time.min, tzinfo=timezone.utc)


def sync_request_id(run_id: str, objeto: HanaObject) -> str:
    """Identificador de job SAP único por `(run, objeto)` y ≤ 36 caracteres.

    El formato anterior (`qa-{run_id}-{objeto}`) truncaba a 36 y `purchase_order` /
    `purchase_order_item` colapsaban en el mismo valor: dos jobs con la misma clave. El hash
    corto va delante del nombre, así que el truncado nunca puede volver a confundirlos.
    """
    hash8 = hashlib.sha1(f"{run_id}:{objeto.value}".encode()).hexdigest()[:8]
    return f"qa-{hash8}-{objeto.value}"[:36]


@dataclass
class Contadores:
    created: int = 0
    existing: int = 0
    updated: int = 0
    skipped: int = 0
    detalle: dict[str, dict[str, int]] = field(default_factory=dict)

    def marcar(self, entidad: str, clave: str) -> None:
        setattr(self, clave, getattr(self, clave) + 1)
        self.detalle.setdefault(entidad, {"created": 0, "existing": 0, "updated": 0, "skipped": 0})[clave] += 1


@dataclass
class Contexto:
    run_id: str
    creds: dict[str, str]
    reset_passwords: bool = False
    companies: dict[str, Company] = field(default_factory=dict)
    users: dict[str, User] = field(default_factory=dict)
    roles: dict[str, Role] = field(default_factory=dict)
    roles_by_id: dict[int, Role] = field(default_factory=dict)
    fases: dict[str, int] = field(default_factory=dict)
    farms: dict[str, Farm] = field(default_factory=dict)
    houses: dict[str, House] = field(default_factory=dict)
    areas: dict[str, Area] = field(default_factory=dict)
    lines: dict[str, GeneticLine] = field(default_factory=dict)
    breeds: dict[str, Breed] = field(default_factory=dict)
    hatcheries: dict[str, Hatchery] = field(default_factory=dict)
    incubators: dict[str, Incubator] = field(default_factory=dict)
    hatchers: dict[str, Hatcher] = field(default_factory=dict)
    catalogs: dict[str, Any] = field(default_factory=dict)
    lots: dict[str, Lot] = field(default_factory=dict)
    sap_refs: dict[str, SapReference] = field(default_factory=dict)
    eventos: dict[str, OperationalEvent] = field(default_factory=dict)
    contadores: Contadores = field(default_factory=Contadores)


class QaBuilder:
    """Construye el dataset QA sobre una sesión; cada fase es idempotente."""

    def __init__(self, db: AsyncSession, ctx: Contexto):
        self.db = db
        self.ctx = ctx
        self.c = ctx.contadores

    # ── utilidades ───────────────────────────────────────────────────────────

    async def _uno(self, consulta):
        return (await self.db.execute(consulta)).scalars().first()

    async def _obtener_o_crear(self, entidad: str, modelo, filtro, **campos):
        fila = await self._uno(select(modelo).where(filtro))
        if fila is None:
            fila = modelo(**campos)
            self.db.add(fila)
            await self.db.flush()
            self.c.marcar(entidad, "created")
        else:
            self.c.marcar(entidad, "existing")
        return fila

    def actor(self, username: str, company: Optional[Company] = None) -> dict:
        u = self.ctx.users[username]
        rol = self.ctx.roles_by_id[u.role_id]
        permisos = {(p.module, p.action.value if hasattr(p.action, "value") else str(p.action)) for p in rol.permissions}
        es_global = any(m == "*" for m, _ in permisos) and rol.company_id is None
        empresa = (company.id if company is not None else u.company_id)
        actor = {"id": u.id, "username": u.username, "first_name": u.first_name, "last_name": u.last_name,
                 "email": u.email, "company_id": empresa, "effective_company_id": empresa, "role_id": u.role_id,
                 "role_name": rol.name, "is_super_admin": es_global, "permissions": permisos}
        set_current_audit_user(actor)
        return actor

    # ── empresas, roles, usuarios, unidades ──────────────────────────────────

    async def empresas(self) -> None:
        for clave, nombre, tax in (("MAIN", COMPANY_MAIN, TAX_MAIN), ("ISO", COMPANY_ISO, TAX_ISO)):
            empresa = await self._obtener_o_crear(
                "companies", Company, Company.tax_id == tax,
                name=nombre, tax_id=tax, country="Venezuela", currency="USD",
                approval_levels=2 if clave == "MAIN" else 1, is_active=True)
            self.ctx.companies[clave] = empresa

    async def roles(self) -> None:
        for nombre in (ROL_ADMIN, ROL_SUP, ROL_APR, ROL_OP, ROL_SAP, ROL_AUD):
            rol = await self._uno(select(Role).where(Role.name == nombre, Role.company_id.is_(None)))
            if rol is None:
                raise RuntimeError(f"Falta el rol canónico '{nombre}': el dataset QA no altera ni crea roles.")
            self.ctx.roles[nombre] = rol
        self.ctx.roles_by_id = {r.id: r for r in self.ctx.roles.values()}
        # Precargar permisos (lazy='selectin' en Role.permissions los trae).
        for r in self.ctx.roles.values():
            await self.db.refresh(r, attribute_names=["permissions"])

    async def usuarios(self) -> None:
        for username, rol, emp, unidades, view, nombre, apellido, _ in USUARIOS:
            empresa = self.ctx.companies[emp]
            clave = self.ctx.creds[username]
            u = await self._uno(select(User).where(User.username == username))
            if u is None:
                u = User(company_id=empresa.id, first_name=nombre, last_name=apellido,
                         email=f"{username}@{EMAIL_DOMAIN}", username=username,
                         hashed_password=hash_password(clave), role_id=self.ctx.roles[rol].id,
                         view_type=view, is_active=True)
                self.db.add(u)
                await self.db.flush()
                self.c.marcar("users", "created")
            else:
                cambios = False
                if u.role_id != self.ctx.roles[rol].id:
                    u.role_id = self.ctx.roles[rol].id; cambios = True
                if u.company_id != empresa.id:
                    u.company_id = empresa.id; cambios = True
                if u.email != f"{username}@{EMAIL_DOMAIN}":
                    u.email = f"{username}@{EMAIL_DOMAIN}"; cambios = True
                if u.first_name != nombre:
                    u.first_name = nombre; cambios = True
                if u.last_name != apellido:
                    u.last_name = apellido; cambios = True
                if u.view_type != view:
                    u.view_type = view; cambios = True
                if not u.is_active:
                    u.is_active = True; cambios = True
                if self.ctx.reset_passwords:
                    u.hashed_password = hash_password(clave); cambios = True
                self.c.marcar("users", "updated" if cambios else "existing")
            self.ctx.users[username] = u
        await self.db.flush()

    async def unidades(self) -> None:
        catalogo = {bu.code: bu for bu in (await self.db.execute(select(BusinessUnit))).scalars().all()}
        habilitacion = {"MAIN": {c: True for c in ALL_BU},
                        "ISO": {"grandparent": False, "breeder": True, "hatchery": False, "broiler": True}}
        cbus: dict[tuple[str, str], CompanyBusinessUnit] = {}
        for emp, config in habilitacion.items():
            empresa = self.ctx.companies[emp]
            for code, on in config.items():
                bu = catalogo[code]
                cbu = await self._uno(select(CompanyBusinessUnit).where(
                    CompanyBusinessUnit.company_id == empresa.id, CompanyBusinessUnit.business_unit_id == bu.id))
                if cbu is None:
                    cbu = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=bu.id, is_enabled=on)
                    self.db.add(cbu); await self.db.flush(); self.c.marcar("company_business_units", "created")
                elif cbu.is_enabled != on:
                    cbu.is_enabled = on; self.c.marcar("company_business_units", "updated")
                else:
                    self.c.marcar("company_business_units", "existing")
                cbus[(emp, code)] = cbu
        for username, _, emp, unidades, *_ in USUARIOS:
            u = self.ctx.users[username]
            for code in unidades:
                cbu = cbus[(emp, code)]
                existente = await self._uno(select(UserBusinessUnit).where(
                    UserBusinessUnit.user_id == u.id, UserBusinessUnit.company_business_unit_id == cbu.id,
                    UserBusinessUnit.revoked_at.is_(None)))
                if existente is None:
                    self.db.add(UserBusinessUnit(user_id=u.id, company_business_unit_id=cbu.id))
                    self.c.marcar("user_business_units", "created")
                else:
                    self.c.marcar("user_business_units", "existing")
        # `R1`: una concesión viva que ya no corresponde (usuario movido de empresa o de unidad) se **revoca**,
        # no se deja activa — una concesión de más es acceso de más.
        esperadas = {username: {cbus[(emp, code)].id for code in units} for username, _, emp, units, *_ in USUARIOS}
        for username, cbus_esperados in esperadas.items():
            vivas = (await self.db.execute(select(UserBusinessUnit).where(
                UserBusinessUnit.user_id == self.ctx.users[username].id,
                UserBusinessUnit.revoked_at.is_(None)))).scalars().all()
            for fila in vivas:
                if fila.company_business_unit_id not in cbus_esperados:
                    fila.revoked_at = datetime.now(timezone.utc)
                    self.c.marcar("user_business_units", "updated")
        await self.db.flush()

    async def pasos_de_aprobacion(self) -> None:
        from app.review.service import ApprovalStepService

        for emp, niveles in (("MAIN", 2), ("ISO", 1)):
            empresa = self.ctx.companies[emp]
            existentes = (await self.db.execute(select(review_models.ApprovalStep).where(
                review_models.ApprovalStep.company_id == empresa.id))).scalars().all()
            if existentes:
                self.c.marcar("approval_steps", "existing"); continue
            await ApprovalStepService(self.db, self.actor("qa.admin", empresa)).seed_default_steps(niveles)
            self.c.marcar("approval_steps", "created")

    # ── maestros ─────────────────────────────────────────────────────────────

    async def fases(self) -> None:
        for code, name, orden, ini, fin in (("CRIA", "Cría", 1, True, False), ("PROD", "Producción", 2, False, False),
                                            ("INCUB", "Incubación", 3, False, False), ("ENGORDE", "Engorde", 4, False, True)):
            fase = await self._uno(select(ProductivePhase).where(ProductivePhase.code == code))
            if fase is None:
                fase = ProductivePhase(name=name, code=code, order=orden, duration_days=140, is_initial=ini, is_final=fin, is_active=True)
                self.db.add(fase); await self.db.flush(); self.c.marcar("productive_phases", "created")
            else:
                self.c.marcar("productive_phases", "existing")
            self.ctx.fases[code] = fase.id

    async def maestros_principal(self) -> None:
        m = self.ctx.companies["MAIN"]
        granjas = (("QA-GP-01", "QA Granja Progenitoras", FarmType.BREEDING, "QA-AREA-GP"),
                   ("QA-BR-01", "QA Granja Reproductoras", FarmType.BREEDING, "QA-AREA-BR"),
                   ("QA-EN-01", "QA Granja Engorde Norte", FarmType.FATTENING, "QA-AREA-ENG"),
                   ("QA-EN-02", "QA Granja Engorde Sur", FarmType.FATTENING, "QA-AREA-ENG"),
                   ("QA-INC-F1", "QA Sede Planta de Incubación", FarmType.MIXED, "QA-AREA-INC"))
        for code, nombre_area in (("QA-AREA-GP", "QA Área Progenitoras"), ("QA-AREA-BR", "QA Área Reproductoras"),
                                  ("QA-AREA-INC", "QA Área Incubación"), ("QA-AREA-ENG", "QA Área Engorde")):
            self.ctx.areas[code] = await self._obtener_o_crear(
                "areas", Area, (Area.company_id == m.id) & (Area.code == code),
                company_id=m.id, name=nombre_area, code=code, description=f"{MARKER} área funcional", is_active=True)
        for code, nombre, tipo, _ in granjas:
            self.ctx.farms[code] = await self._obtener_o_crear(
                "farms", Farm, (Farm.company_id == m.id) & (Farm.code == code),
                company_id=m.id, name=nombre, code=code, location=f"{MARKER} · ubicación sintética", farm_type=tipo, is_active=True)
        capacidades = ((1, 12000, HouseType.CLOSED), (2, 18000, HouseType.OPEN), (3, 25000, HouseType.TUNNEL))
        for code, *_ in granjas:
            granja = self.ctx.farms[code]
            n_galpones = 2 if code == "QA-INC-F1" else 3
            for i, cap, tipo in capacidades[:n_galpones]:
                nombre = f"{code}-G{i}"
                self.ctx.houses[nombre] = await self._obtener_o_crear(
                    "houses", House, (House.farm_id == granja.id) & (House.name == nombre),
                    farm_id=granja.id, name=nombre, capacity=cap, house_type=tipo, is_active=True)
        # Galpón inactivo para pruebas negativas.
        gp = self.ctx.farms["QA-GP-01"]
        self.ctx.houses["QA-GP-01-GX"] = await self._obtener_o_crear(
            "houses", House, (House.farm_id == gp.id) & (House.name == "QA-GP-01-GX (inactivo)"),
            farm_id=gp.id, name="QA-GP-01-GX (inactivo)", capacity=5000, house_type=HouseType.OPEN, is_active=False)

        # Genética: una línea por cadena, raza y curva activa.
        for code, nombre, bu in (("QA-LINE-GP", "QA Línea Progenitoras", "grandparent"),
                                 ("QA-LINE-BR", "QA Línea Reproductoras", "breeder"),
                                 ("QA-LINE-BRO", "QA Línea Engorde", "broiler")):
            linea = await self._obtener_o_crear(
                "genetic_lines", GeneticLine, (GeneticLine.company_id == m.id) & (GeneticLine.code == code),
                company_id=m.id, name=nombre, code=code, supplier="QA Genética Internacional", description=MARKER, is_active=True)
            self.ctx.lines[code] = linea
            raza = await self._obtener_o_crear(
                "breeds", Breed, (Breed.genetic_line_id == linea.id) & (Breed.name == f"QA Raza {bu.title()}"),
                genetic_line_id=linea.id, name=f"QA Raza {bu.title()}", bird_type=BirdTypeEnum(bu), description=MARKER, is_active=True)
            self.ctx.breeds[code] = raza
            curva = await self._uno(select(GeneticWeightCurve).where(
                GeneticWeightCurve.genetic_line_id == linea.id, GeneticWeightCurve.version_label == f"{VERSION}"))
            if curva is None:
                curva = GeneticWeightCurve(genetic_line_id=linea.id, version_label=VERSION, is_active=True, source=MARKER)
                self.db.add(curva); await self.db.flush()
                puntos = self._puntos_de_curva(bu)
                for edad, objetivo in puntos:
                    self.db.add(GeneticWeightCurvePoint(curve_id=curva.id, age_days=edad, target_weight=objetivo,
                                                        min_weight=round(objetivo * 0.92, 1), max_weight=round(objetivo * 1.08, 1)))
                self.c.marcar("genetic_weight_curves", "created")
            else:
                self.c.marcar("genetic_weight_curves", "existing")

        # Planta de incubación y equipos.
        planta = await self._obtener_o_crear(
            "hatcheries", Hatchery, (Hatchery.company_id == m.id) & (Hatchery.code == "QA-INC-01"),
            company_id=m.id, name="QA Planta Incubación Central", code="QA-INC-01", location=f"{MARKER} · planta sintética", is_active=True)
        self.ctx.hatcheries["QA-INC-01"] = planta
        for nombre, cap, activo in (("QA Incubadora A1", 115200, True), ("QA Incubadora A2", 57600, True),
                                    ("QA Incubadora A3", 19200, True), ("QA Incubadora A4 (inactiva)", 19200, False)):
            self.ctx.incubators[nombre] = await self._obtener_o_crear(
                "incubators", Incubator, (Incubator.hatchery_id == planta.id) & (Incubator.name == nombre),
                hatchery_id=planta.id, name=nombre, capacity=cap, is_active=activo)
        for nombre, cap in (("QA Nacedora N1", 38400), ("QA Nacedora N2", 19200)):
            self.ctx.hatchers[nombre] = await self._obtener_o_crear(
                "hatchers", Hatcher, (Hatcher.hatchery_id == planta.id) & (Hatcher.name == nombre),
                hatchery_id=planta.id, name=nombre, capacity=cap, is_active=True)

        await self._catalogos(m, principal=True)

    def _puntos_de_curva(self, bu: str) -> list[tuple[int, float]]:
        if bu == "broiler":
            return [(0, 42), (7, 180), (14, 450), (21, 900), (28, 1450), (35, 2050), (42, 2650), (49, 3200)]
        base = [(0, 40), (7, 110), (14, 230), (21, 380), (28, 540), (35, 700), (42, 860), (56, 1150), (70, 1450),
                (84, 1750), (98, 2050), (112, 2350), (126, 2650), (140, 2950), (168, 3200), (196, 3350), (280, 3500)]
        return base if bu == "breeder" else [(a, round(p * 1.05)) for a, p in base]

    async def _catalogos(self, empresa: Company, *, principal: bool) -> None:
        def cat(modelo, nombre, **extra):
            return self._obtener_o_crear(modelo.__tablename__, modelo,
                                         (modelo.company_id == empresa.id) & (modelo.name == nombre),
                                         company_id=empresa.id, name=nombre, is_active=True, **extra)

        p = "P" if principal else "I"
        proveedores = (("QA Genética Internacional", "genetica", "Francia"), ("QA Alimentos Balanceados", "alimento", "Venezuela"),
                       ("QA Laboratorio Vacunas", "vacunas", "Brasil"), ("QA Farmacéutica Avícola", "medicamentos", "Colombia"),
                       ("QA Insumos de Incubación", "insumos", "Venezuela"))
        if not principal:
            proveedores = proveedores[:2]
        for i, (nombre, tipo, pais) in enumerate(proveedores, start=1):
            self.ctx.catalogs[f"supplier:{empresa.id}:{tipo}"] = await cat(
                Supplier, nombre, sap_code=f"QA-VEND-{p}{i:02d}", country=pais, supplier_type=tipo)
        for i, placa in enumerate(("QA-TR-001", "QA-TR-002", "QA-TR-003")[: 3 if principal else 1], start=1):
            self.ctx.catalogs[f"transport:{empresa.id}:{i}"] = await cat(
                Transport, f"QA Transporte {i:02d}", plate=placa, transport_type="camión climatizado" if i < 3 else "camión jaulero", capacity=8000 * i)
        for i, nombre in enumerate(("QA Planta de Beneficio Norte", "QA Planta de Beneficio Sur")[: 2 if principal else 1], start=1):
            self.ctx.catalogs[f"plant:{empresa.id}:{i}"] = await cat(ProcessingPlant, nombre, location=f"{MARKER} planta {i}")
        for i, (nombre, code, pres) in enumerate((("QA Preiniciador", "QA-FEED-PRE", "saco 40 kg"), ("QA Iniciador", "QA-FEED-INI", "saco 40 kg"),
                                                   ("QA Crecimiento", "QA-FEED-CRE", "saco 40 kg"), ("QA Postura", "QA-FEED-POS", "granel"))[: 4 if principal else 1], start=1):
            self.ctx.catalogs[f"feed:{empresa.id}:{i}"] = await cat(FeedType, nombre, code=code, presentation=pres)
        for i, (nombre, ruta) in enumerate((("QA Vacuna Newcastle", "water"), ("QA Vacuna Gumboro", "water"),
                                             ("QA Vacuna Marek", "injection"), ("QA Vacuna Bronquitis", "spray"))[: 4 if principal else 1], start=1):
            self.ctx.catalogs[f"vaccine:{empresa.id}:{i}"] = await cat(Vaccine, nombre, laboratory="QA Laboratorio", vaccine_type="viva", standard_dosage="1 dosis/ave", application_route=ruta)
        for i, nombre in enumerate(("QA Antibiótico Amplio", "QA Vitaminas Electrolitos", "QA Antiparasitario")[: 3 if principal else 1], start=1):
            self.ctx.catalogs[f"medication:{empresa.id}:{i}"] = await cat(Medication, nombre, laboratory="QA Farmacéutica", presentation="frasco 1 L")
        for i, (nombre, categoria) in enumerate((("QA Mortalidad súbita", "sanitaria"), ("QA Problema respiratorio", "sanitaria"),
                                                  ("QA Golpe de calor", "ambiental"), ("QA Aplastamiento", "manejo"))[: 4 if principal else 1], start=1):
            self.ctx.catalogs[f"mortality_cause:{empresa.id}:{i}"] = await cat(MortalityCause, nombre, category=categoria)
        for i, (nombre, categoria) in enumerate((("QA Bajo peso", "productiva"), ("QA Problema de patas", "sanitaria"), ("QA Mal sexado", "productiva"))[: 3 if principal else 1], start=1):
            self.ctx.catalogs[f"cull_cause:{empresa.id}:{i}"] = await cat(CullCause, nombre, category=categoria)
        if principal:
            for i, (nombre, categoria) in enumerate((("QA Dato inconsistente", "datos"), ("QA Falta evidencia", "documental"), ("QA Fecha incorrecta", "datos")), start=1):
                self.ctx.catalogs[f"rejection_reason:{empresa.id}:{i}"] = await cat(RejectionReason, nombre, category=categoria, description=MARKER)
            for i, nombre in enumerate(("QA Error de digitación", "QA Cambio de fecha", "QA Ajuste de cantidad"), start=1):
                self.ctx.catalogs[f"correction_type:{empresa.id}:{i}"] = await cat(CorrectionType, nombre, description=MARKER)

    async def maestros_aislamiento(self) -> None:
        iso = self.ctx.companies["ISO"]
        self.ctx.areas["QA-ISO-AREA"] = await self._obtener_o_crear(
            "areas", Area, (Area.company_id == iso.id) & (Area.code == "QA-ISO-AREA"),
            company_id=iso.id, name="QA Área Aislamiento", code="QA-ISO-AREA", is_active=True)
        granja = await self._obtener_o_crear(
            "farms", Farm, (Farm.company_id == iso.id) & (Farm.code == "QA-ISO-F1"),
            company_id=iso.id, name="QA Granja Aislamiento", code="QA-ISO-F1", location=f"{MARKER} aislamiento", farm_type=FarmType.MIXED, is_active=True)
        self.ctx.farms["QA-ISO-F1"] = granja
        for i in (1, 2):
            nombre = f"QA-ISO-F1-G{i}"
            self.ctx.houses[nombre] = await self._obtener_o_crear(
                "houses", House, (House.farm_id == granja.id) & (House.name == nombre),
                farm_id=granja.id, name=nombre, capacity=10000, house_type=HouseType.OPEN, is_active=True)
        await self._catalogos(iso, principal=False)

    # ── SAP sintético ────────────────────────────────────────────────────────

    def _filas_sap(self) -> dict[HanaObject, list[dict]]:
        """Filas con nombres de campo SAP (lo que leería el inbound) — todas `QA-`, sociedad QA01/QA02."""
        H = hoy().strftime("%Y%m%d")
        d = lambda n: D(n).strftime("%Y%m%d")  # noqa: E731
        M = SAP_CLIENT
        plantas = (("QAP1", "QA Planta Progenitoras", "QA-GP-01"), ("QAP2", "QA Planta Reproductoras", "QA-BR-01"),
                   ("QAP3", "QA Planta Incubadora", "QA-INC-F1"), ("QAP4", "QA Planta Engorde Norte", "QA-EN-01"),
                   ("QAP5", "QA Planta Engorde Sur", "QA-EN-02"))
        materiales = (("QA-MAT-GP-AVES", "Abuelas día 1 (QA)", "HAWA", "UN"), ("QA-MAT-BR-AVES", "Reproductoras día 1 (QA)", "HAWA", "UN"),
                      ("QA-MAT-POLLITO", "Pollito de engorde (QA)", "FERT", "UN"), ("QA-MAT-HUEVO-FERTIL", "Huevo fértil (QA)", "FERT", "UN"),
                      ("QA-MAT-FEED-INI", "Alimento iniciador (QA)", "ROH", "KG"), ("QA-MAT-FEED-CRE", "Alimento crecimiento (QA)", "ROH", "KG"),
                      ("QA-MAT-VAC-NEW", "Vacuna Newcastle (QA)", "ROH", "UN"), ("QA-MAT-MED-AMP", "Antibiótico amplio (QA)", "ROH", "UN"),
                      ("QA-MAT-INS-INC", "Insumos de incubación (QA)", "ROH", "UN"))
        proveedores = (("QA-VEND-P01", "QA Genética Internacional", "FR"), ("QA-VEND-P02", "QA Alimentos Balanceados", "VE"),
                       ("QA-VEND-P03", "QA Laboratorio Vacunas", "BR"), ("QA-VEND-P04", "QA Farmacéutica Avícola", "CO"),
                       ("QA-VEND-P05", "QA Insumos de Incubación", "VE"))
        # OC: (EBELN, proveedor, posiciones[(material, planta, cantidad, unidad)], descripción)
        ocs = (
            ("QA-OC-GP-AVES-001", "QA-VEND-P01", [("QA-MAT-GP-AVES", "QAP1", 5000, "UN")]),            # BR-18 OC-1: recibido 0
            ("QA-OC-BR-AVES-002", "QA-VEND-P01", [("QA-MAT-BR-AVES", "QAP2", 10000, "UN")]),           # OC-2: parcial (5000)
            ("QA-OC-BRO-AVES-003", "QA-VEND-P01", [("QA-MAT-POLLITO", "QAP4", 10000, "UN")]),          # OC-3: completa
            ("QA-OC-BRO-AVES-004", "QA-VEND-P01", [("QA-MAT-POLLITO", "QAP4", 12500, "UN")]),          # OC-4: con reverso
            ("QA-OC-GP-IMPORT-005", "QA-VEND-P01", [("QA-MAT-GP-AVES", "QAP1", 6000, "UN")]),          # importación GP
            ("QA-OC-FEED-006", "QA-VEND-P02", [("QA-MAT-FEED-INI", "QAP2", 40000, "KG"), ("QA-MAT-FEED-CRE", "QAP2", 60000, "KG")]),
            ("QA-OC-VAC-007", "QA-VEND-P03", [("QA-MAT-VAC-NEW", "QAP1", 20000, "UN")]),
            ("QA-OC-MED-008", "QA-VEND-P04", [("QA-MAT-MED-AMP", "QAP4", 300, "UN")]),
            ("QA-OC-INC-009", "QA-VEND-P05", [("QA-MAT-INS-INC", "QAP3", 5000, "UN")]),
            ("QA-OC-FEED-BRO-010", "QA-VEND-P02", [("QA-MAT-FEED-CRE", "QAP4", 80000, "KG")]),
            ("QA-OC-BR18-TEST", "QA-VEND-P01", [("QA-MAT-BR-AVES", "QAP2", 1000, "UN")]),               # §72: 300/700/1
        )
        filas: dict[HanaObject, list[dict]] = {o: [] for o in HanaObject}
        filas[HanaObject.COMPANY] += [{"MANDT": M, "BUKRS": "QA01", "BUTXT": COMPANY_MAIN, "ORT01": "Caracas", "LAND1": "VE", "WAERS": "USD"},
                                      {"MANDT": M, "BUKRS": "QA02", "BUTXT": COMPANY_ISO, "ORT01": "Valencia", "LAND1": "VE", "WAERS": "USD"}]
        for werks, nombre, _ in plantas:
            filas[HanaObject.PLANT].append({"MANDT": M, "WERKS": werks, "NAME1": nombre, "NAME2": MARKER, "ORT01": "Caracas", "LAND1": "VE", "BUKRS": "QA01"})
            filas[HanaObject.STORAGE_LOCATION].append({"MANDT": M, "WERKS": werks, "LGORT": "0001", "LGOBE": f"Almacén principal {werks}", "BUKRS": "QA01"})
        filas[HanaObject.PLANT].append({"MANDT": M, "WERKS": "QAP9", "NAME1": "QA Planta Aislamiento", "ORT01": "Valencia", "LAND1": "VE", "BUKRS": "QA02"})
        filas[HanaObject.PLANT].append({"MANDT": M, "WERKS": "QAP7", "NAME1": "QA Planta sin mapping (pendiente)", "ORT01": "Maracay", "LAND1": "VE", "BUKRS": "QA01"})
        for lifnr, nombre, pais in proveedores:
            filas[HanaObject.VENDOR].append({"MANDT": M, "LIFNR": lifnr, "NAME1": nombre, "STCD1": f"J-QA{lifnr[-2:]}", "LAND1": pais, "BUKRS": "QA01"})
        for matnr, desc, tipo, um in materiales:
            filas[HanaObject.MATERIAL].append({"MANDT": M, "MATNR": matnr, "MAKTX": desc, "MTART": tipo, "MATKL": "QA", "MEINS": um, "LAEDA": d(30)})
        filas[HanaObject.MATERIAL].append({"MANDT": M, "MATNR": "QA-MAT-INVALIDO", "MAKTX": "Material sin unidad (ejemplo de error)", "MTART": "ROH", "LAEDA": d(30)})
        for i, (matnr, _, _, _) in enumerate(materiales[:4], start=1):
            filas[HanaObject.BATCH].append({"MANDT": M, "MATNR": matnr, "WERKS": "QAP1" if i < 3 else "QAP3", "CHARG": f"QA-LOTE-{i:03d}",
                                            "HSDAT": d(40), "VFDAT": d(-200), "ERSDA": d(40), "BUKRS": "QA01"})
        for bwart, texto in (("101", "Entrada de mercancía por OC"), ("102", "Anulación entrada por OC"), ("261", "Consumo para orden"),
                             ("303", "Traslado planta a planta (salida)"), ("641", "Traslado en tránsito (STO)")):
            filas[HanaObject.MOVEMENT_TYPE].append({"MANDT": M, "BWART": bwart, "BTEXT": texto})
        for i, (ebeln, lifnr, posiciones) in enumerate(ocs, start=1):
            filas[HanaObject.PURCHASE_ORDER].append({"MANDT": M, "EBELN": ebeln, "BUKRS": "QA01", "BSTYP": "F", "BSART": "NB", "LIFNR": lifnr,
                                                     "EKORG": "QA01", "BEDAT": d(45 - i), "AEDAT": d(45 - i), "WAERS": "USD"})
            for j, (matnr, werks, cant, um) in enumerate(posiciones, start=1):
                filas[HanaObject.PURCHASE_ORDER_ITEM].append({"MANDT": M, "EBELN": ebeln, "EBELP": f"{j * 10:05d}", "MATNR": matnr, "TXZ01": matnr,
                                                              "WERKS": werks, "LGORT": "0001", "MENGE": cant, "MEINS": um, "EINDT": d(20), "BUKRS": "QA01"})
        # Historial de OC: recepciones 101 (y el reverso 102 de OC-4) — informativo, STAGING_ONLY.
        historial = (("QA-OC-BR-AVES-002", "00010", "5000000101", "S", 5000, d(56)), ("QA-OC-BRO-AVES-003", "00010", "5000000102", "S", 10000, d(6)),
                     ("QA-OC-BRO-AVES-004", "00010", "5000000103", "S", 12000, d(28)), ("QA-OC-BRO-AVES-004", "00010", "5000000104", "S", 500, d(27)),
                     ("QA-OC-BRO-AVES-004", "00010", "5000000105", "H", 500, d(26)))
        for ebeln, ebelp, belnr, shkzg, cant, fecha in historial:
            filas[HanaObject.PURCHASE_ORDER_HISTORY].append({"MANDT": M, "EBELN": ebeln, "EBELP": ebelp, "ZEKKN": "00", "VGABE": "1", "GJAHR": fecha[:4],
                                                             "BELNR": belnr, "BUZEI": "0001", "BEWTP": "E", "BWART": "101" if shkzg == "S" else "102",
                                                             "BUDAT": fecha, "MENGE": cant, "SHKZG": shkzg, "MATNR": "QA-MAT-POLLITO", "WERKS": "QAP4",
                                                             "BUKRS": "QA01"})
        for i, (aufnr, werks, matnr, cant, fase) in enumerate((("QA-OP-GP-001", "QAP1", "QA-MAT-HUEVO-FERTIL", 180000, "PHAS1"),
                                                               ("QA-OP-BR-001", "QAP2", "QA-MAT-HUEVO-FERTIL", 240000, "PHAS1"),
                                                               ("QA-OP-INC-001", "QAP3", "QA-MAT-POLLITO", 60000, "PHAS2"),
                                                               ("QA-OP-BRO-001", "QAP4", "QA-MAT-POLLITO", 30000, "PHAS3")), start=1):
            fila = {"MANDT": M, "AUFNR": aufnr, "AUART": "PP01", "BUKRS": "QA01", "WERKS": werks, "MATNR": matnr, "LGORT": "0001",
                    "GSTRP": d(40), "GLTRP": d(-30), "GAMNG": cant, "GMEIN": "UN", "ERDAT": d(41), "AEDAT": d(10), fase: "X"}
            filas[HanaObject.PRODUCTION_ORDER].append(fila)
        stos = (("QA-STO-GP-HAT-001", "QAP1", "QAP3", "QA-MAT-HUEVO-FERTIL", 20000, "UN"), ("QA-STO-BR-HAT-001", "QAP2", "QAP3", "QA-MAT-HUEVO-FERTIL", 30000, "UN"),
                ("QA-STO-HAT-BRO-001", "QAP3", "QAP4", "QA-MAT-POLLITO", 10000, "UN"), ("QA-STO-FEED-001", "QAP2", "QAP4", "QA-MAT-FEED-CRE", 15000, "KG"),
                ("QA-STO-VAC-001", "QAP1", "QAP2", "QA-MAT-VAC-NEW", 5000, "UN"), ("QA-STO-MED-001", "QAP4", "QAP5", "QA-MAT-MED-AMP", 50, "UN"))
        for ebeln, origen, destino, matnr, cant, um in stos:
            filas[HanaObject.TRANSFER_ORDER].append({"MANDT": M, "EBELN": ebeln, "EBELP": "00010", "BUKRS": "QA01", "BSART": "UB", "RESWK": origen,
                                                     "RESLO": "0001", "WERKS": destino, "LGORT": "0001", "MATNR": matnr, "TXZ01": matnr, "MENGE": cant,
                                                     "MEINS": um, "BEDAT": d(15), "AEDAT": d(15)})
        for i, (vbeln, matnr, cant, um, salida) in enumerate((("QA-ENT-001", "QA-MAT-POLLITO", 8000, "UN", d(3)), ("QA-ENT-002", "QA-MAT-HUEVO-FERTIL", 12000, "UN", "")), start=1):
            filas[HanaObject.OUTBOUND_ORDER].append({"MANDT": M, "VBELN": vbeln, "POSNR": "000010", "LFART": "LF", "VSTEL": "QAP4", "KUNNR": f"QA-CLI-{i:03d}",
                                                     "WADAT": d(2), "WADAT_IST": salida, "ERDAT": d(5), "MATNR": matnr, "ARKTX": matnr, "WERKS": "QAP4",
                                                     "LGORT": "0001", "LFIMG": cant, "VRKME": um, "BUKRS": "QA01"})
        movimientos = (("QA-MD-0001", "101", "QA-MAT-BR-AVES", "QAP2", None, 5000, "S", "QA-OC-BR-AVES-002", d(56), None),
                       ("QA-MD-0002", "101", "QA-MAT-POLLITO", "QAP4", None, 10000, "S", "QA-OC-BRO-AVES-003", d(6), None),
                       ("QA-MD-0003", "101", "QA-MAT-POLLITO", "QAP4", None, 500, "S", "QA-OC-BRO-AVES-004", d(27), None),
                       ("QA-MD-0004", "102", "QA-MAT-POLLITO", "QAP4", None, 500, "H", "QA-OC-BRO-AVES-004", d(26), "QA-MD-0003"),
                       ("QA-MD-0005", "261", "QA-MAT-FEED-CRE", "QAP4", None, 4000, "H", None, d(21), None),
                       ("QA-MD-0006", "303", "QA-MAT-FEED-CRE", "QAP2", "QAP4", 15000, "H", None, d(14), None),
                       ("QA-MD-0007", "641", "QA-MAT-HUEVO-FERTIL", "QAP2", "QAP3", 30000, "H", None, d(13), None))
        for mblnr, bwart, matnr, werks, umwrk, cant, shkzg, ebeln, fecha, anulado in movimientos:
            fila = {"MANDT": M, "MBLNR": mblnr, "MJAHR": fecha[:4], "ZEILE": "0001", "BWART": bwart, "MATNR": matnr, "WERKS": werks, "LGORT": "0001",
                    "ERFMG": cant, "ERFME": "KG" if "FEED" in matnr else "UN", "MENGE": cant, "MEINS": "KG" if "FEED" in matnr else "UN",
                    "SHKZG": shkzg, "BUDAT": fecha, "BLDAT": fecha, "CPUDT": fecha, "BUKRS": "QA01"}
            if umwrk:
                fila.update(UMWRK=umwrk, UMLGO="0001")
            if ebeln:
                fila.update(EBELN=ebeln, EBELP="00010")
            if anulado:
                fila.update(SMBLN=anulado, SJAHR=fecha[:4], SMBLP="0001")
            if bwart == "261":
                fila["AUFNR"] = "QA-OP-BRO-001"
            filas[HanaObject.MATERIAL_MOVEMENT].append(fila)
        self._plantas_sap = plantas
        return filas

    async def sap_sintetico(self) -> None:
        m, iso = self.ctx.companies["MAIN"], self.ctx.companies["ISO"]
        actor_sap = self.ctx.users["qa.sap"]
        filas = self._filas_sap()
        # Mappings MANDT → BUKRS → WERKS → empresa (QAP7 queda a propósito sin mapping).
        async def mapping(entity, key, parent, company, farm_id=None, bu=None):
            fila = await self._uno(select(SapEntityMapping).where(
                SapEntityMapping.source_system == SAP_SOURCE, SapEntityMapping.client == SAP_CLIENT,
                SapEntityMapping.entity_type == entity, SapEntityMapping.sap_key == key))
            if fila is None:
                self.db.add(SapEntityMapping(source_system=SAP_SOURCE, client=SAP_CLIENT, entity_type=entity, sap_key=key, parent_sap_key=parent,
                                             company_id=company.id, farm_id=farm_id, business_unit_code=bu, is_active=True, created_by_id=actor_sap.id))
                self.c.marcar("sap_entity_mappings", "created")
            else:
                self.c.marcar("sap_entity_mappings", "existing")
        await mapping("COMPANY_CODE", "QA01", None, m)
        await mapping("COMPANY_CODE", "QA02", None, iso)
        bu_por_planta = {"QAP1": "grandparent", "QAP2": "breeder", "QAP3": "hatchery", "QAP4": "broiler", "QAP5": "broiler"}
        for werks, _, granja in self._plantas_sap:
            await mapping("PLANT", werks, "QA01", m, farm_id=self.ctx.farms[granja].id, bu=bu_por_planta[werks])
            await mapping("STORAGE_LOCATION", f"{werks}/0001", werks, m)
        await mapping("PLANT", "QAP9", "QA02", iso, farm_id=self.ctx.farms["QA-ISO-F1"].id, bu="breeder")
        await self.db.flush()
        mapeadas = {"QAP1", "QAP2", "QAP3", "QAP4", "QAP5"}

        promovibles = {HanaObject.PLANT: SapReferenceType.PLANT, HanaObject.STORAGE_LOCATION: SapReferenceType.STORAGE_LOCATION,
                       HanaObject.VENDOR: SapReferenceType.VENDOR, HanaObject.MATERIAL: SapReferenceType.MATERIAL,
                       HanaObject.BATCH: SapReferenceType.SAP_BATCH}
        for objeto in HanaObject:
            definicion = get_definition(objeto)
            job = await self._uno(select(SapInboundSyncJob).where(
                SapInboundSyncJob.company_id == m.id, SapInboundSyncJob.source_system == SAP_SOURCE,
                SapInboundSyncJob.object_type == objeto.value))
            if job is None:
                job = SapInboundSyncJob(sync_request_id=sync_request_id(self.ctx.run_id, objeto), company_id=m.id, source_system=SAP_SOURCE,
                                        object_type=objeto.value, query_id=definicion.query_id, trigger="manual", status=JOB_COMPLETED,
                                        filters={"marker": MARKER, "note": "dataset QA sintético: ningún acceso a SAP HANA"},
                                        initiated_by_id=actor_sap.id, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))
                self.db.add(job); await self.db.flush(); self.c.marcar("sap_inbound_sync_jobs", "created")
            else:
                self.c.marcar("sap_inbound_sync_jobs", "existing")
            contadores = {"read": 0, "valid": 0, "invalid": 0, "pending": 0, "promoted": 0}
            for fila in filas[objeto]:
                sociedad = fila.get("BUKRS")
                empresa = iso if sociedad == "QA02" else m
                clave = source_key(definicion, fila)
                rec = await self._uno(select(SapInboundRecord).where(
                    SapInboundRecord.company_id == empresa.id, SapInboundRecord.source_system == SAP_SOURCE,
                    SapInboundRecord.object_type == objeto.value, SapInboundRecord.source_key == clave, SapInboundRecord.is_current.is_(True)))
                contadores["read"] += 1
                if rec is not None:
                    self.c.marcar("sap_inbound_records", "existing"); continue
                staged = stage(objeto, fila)
                validacion = V_INVALID if staged.errors else V_VALID
                plantas_fila = [p for p in staged.plants if p]
                pendiente = any(p not in mapeadas and p != "QAP9" for p in plantas_fila)
                mapping_status = M_PENDING_MAPPING if pendiente else M_MAPPED
                rec = SapInboundRecord(sync_job_id=job.id, company_id=empresa.id, source_system=SAP_SOURCE, object_type=objeto.value,
                                       source_key=clave, client=SAP_CLIENT, company_code=sociedad, plant_code=plantas_fila[0] if plantas_fila else None,
                                       payload_json=fila, payload_hash=canonical_hash(fila), version=1, is_current=True,
                                       extracted_at=datetime.now(timezone.utc), validation_status=validacion, mapping_status=mapping_status,
                                       staged_json=staged.dto if not staged.errors else None,
                                       error_code="SAP_VALIDATION_ERROR" if staged.errors else ("SAP_MAPPING_PENDING" if pendiente else None),
                                       error_message="; ".join(staged.errors) if staged.errors else (
                                           f"centro {plantas_fila[0]} sin mapping a esta empresa" if pendiente else None))
                self.db.add(rec); await self.db.flush()
                self.c.marcar("sap_inbound_records", "created")
                if staged.errors:
                    contadores["invalid"] += 1; rec.promotion_status = P_STAGED_ONLY; continue
                if pendiente:
                    contadores["pending"] += 1; rec.promotion_status = P_STAGED_ONLY; continue
                contadores["valid"] += 1
                if objeto in promovibles:
                    ref = await self._promover_simple(objeto, promovibles[objeto], rec, empresa, actor_sap)
                    rec.promotion_status, rec.promoted_reference_id = P_PROMOTED, ref.id
                    contadores["promoted"] += 1
                else:
                    rec.promotion_status = P_STAGED_ONLY
            job.rows_read, job.rows_valid, job.rows_invalid = contadores["read"], contadores["valid"], contadores["invalid"]
            job.rows_pending_mapping, job.rows_promoted, job.rows_raw = contadores["pending"], contadores["promoted"], contadores["read"]
        # Documentos compuestos: OC (cabecera + posiciones) y STO (posiciones).
        await self._promover_documentos(filas, m, actor_sap)
        # OC propia de la empresa de aislamiento (referencia directa, para su recepción).
        ref, _ = await upsert_reference(self.db, company_id=iso.id, ref_type=SapReferenceType.PURCHASE_ORDER, sap_code="QA-ISO-OC-001",
                                        description="OC aves engorde (empresa de aislamiento, QA sintética)", quantity=4000, unit="UN",
                                        extra={"source": SAP_SOURCE, "marker": MARKER, "run_id": self.ctx.run_id, "company_code": "QA02"},
                                        actor_id=actor_sap.id)
        self.ctx.sap_refs["QA-ISO-OC-001"] = ref
        await self.db.flush()

    async def _promover_simple(self, objeto, ref_type, rec, empresa, actor_sap) -> SapReference:
        s = rec.staged_json
        extra = {"source": SAP_SOURCE, "marker": MARKER, "run_id": self.ctx.run_id, "client": rec.client,
                 "company_code": rec.company_code, "inbound_record_id": rec.id, "payload_hash": rec.payload_hash}
        if objeto is HanaObject.PLANT:
            codigo, desc = s["plant"], s["name"]; extra.update(city=s.get("city"), country=s.get("country"))
        elif objeto is HanaObject.STORAGE_LOCATION:
            codigo, desc = f"{s['plant']}-{s['storage_location']}", s.get("name") or s["storage_location"]
            extra.update(plant=s["plant"], storage_location=s["storage_location"])
        elif objeto is HanaObject.VENDOR:
            codigo, desc = s["vendor"], s["name"]; extra.update(tax_id=s.get("tax_id"), country=s.get("country"), vendor_name=s["name"])
        elif objeto is HanaObject.MATERIAL:
            codigo, desc = s["material"], s.get("description") or s["material"]
            extra.update(material_type=s.get("material_type"), base_unit=s.get("base_unit"))
        else:
            codigo, desc = f"{s['material']}/{s['plant']}/{s['batch']}", f"Lote SAP {s['batch']} de {s['material']}"
            extra.update(material=s["material"], plant=s["plant"], batch=s["batch"], expiry_date=s.get("expiry_date"))
        existente = await self._uno(select(SapReference).where(SapReference.company_id == empresa.id, SapReference.ref_type == ref_type,
                                                              SapReference.sap_code == codigo))
        ref, motivo = await upsert_reference(self.db, company_id=empresa.id, ref_type=ref_type, sap_code=codigo, description=desc,
                                             quantity=None, unit=None, extra=extra, actor_id=actor_sap.id)
        if ref is None:
            raise RuntimeError(f"no se pudo promover {codigo}: {motivo}")
        self.c.marcar("sap_references", "existing" if existente is not None else "created")
        self.ctx.sap_refs[codigo] = ref
        return ref

    async def _promover_documentos(self, filas, empresa, actor_sap) -> None:
        posiciones: dict[str, list[dict]] = {}
        for fila in filas[HanaObject.PURCHASE_ORDER_ITEM]:
            posiciones.setdefault(fila["EBELN"], []).append(fila)
        vendedores = {v["LIFNR"]: v["NAME1"] for v in filas[HanaObject.VENDOR]}
        for cab in filas[HanaObject.PURCHASE_ORDER]:
            ebeln = cab["EBELN"]
            items = posiciones.get(ebeln, [])
            unidades = {i["MEINS"] for i in items}
            total = sum(i["MENGE"] for i in items) if len(unidades) == 1 else None
            existente = await self._uno(select(SapReference).where(SapReference.company_id == empresa.id,
                                                                  SapReference.ref_type == SapReferenceType.PURCHASE_ORDER, SapReference.sap_code == ebeln))
            ref, motivo = await upsert_reference(
                self.db, company_id=empresa.id, ref_type=SapReferenceType.PURCHASE_ORDER, sap_code=ebeln,
                description=f"OC {ebeln} · {vendedores.get(cab['LIFNR'], cab['LIFNR'])} · {', '.join(i['MATNR'] for i in items)}",
                quantity=total, unit=next(iter(unidades)) if len(unidades) == 1 else None,
                extra={"source": SAP_SOURCE, "marker": MARKER, "run_id": self.ctx.run_id, "client": SAP_CLIENT, "company_code": "QA01",
                       "vendor": cab["LIFNR"], "vendor_name": vendedores.get(cab["LIFNR"]), "document_date": cab["BEDAT"], "status": "OPEN",
                       "items": [{"item": i["EBELP"], "material": i["MATNR"], "plant": i["WERKS"], "quantity": i["MENGE"], "unit": i["MEINS"]} for i in items]},
                actor_id=actor_sap.id)
            if ref is None:
                raise RuntimeError(f"OC {ebeln}: {motivo}")
            self.c.marcar("sap_references", "existing" if existente is not None else "created")
            self.ctx.sap_refs[ebeln] = ref
            await self._marcar_promovida(empresa, HanaObject.PURCHASE_ORDER, ref, ebeln)
        for sto in filas[HanaObject.TRANSFER_ORDER]:
            ebeln = sto["EBELN"]
            existente = await self._uno(select(SapReference).where(SapReference.company_id == empresa.id,
                                                                  SapReference.ref_type == SapReferenceType.TRANSFER_ORDER, SapReference.sap_code == ebeln))
            ref, motivo = await upsert_reference(
                self.db, company_id=empresa.id, ref_type=SapReferenceType.TRANSFER_ORDER, sap_code=ebeln,
                description=f"STO {ebeln} · {sto['MATNR']} · {sto['RESWK']} → {sto['WERKS']}", quantity=sto["MENGE"], unit=sto["MEINS"],
                extra={"source": SAP_SOURCE, "marker": MARKER, "run_id": self.ctx.run_id, "client": SAP_CLIENT, "company_code": "QA01",
                       "source_plant": sto["RESWK"], "destination_plant": sto["WERKS"], "material": sto["MATNR"], "document_type": "UB", "status": "OPEN"},
                actor_id=actor_sap.id)
            if ref is None:
                raise RuntimeError(f"STO {ebeln}: {motivo}")
            self.c.marcar("sap_references", "existing" if existente is not None else "created")
            self.ctx.sap_refs[ebeln] = ref
            await self._marcar_promovida(empresa, HanaObject.TRANSFER_ORDER, ref, ebeln)

    async def _marcar_promovida(self, empresa, objeto, ref, ebeln) -> None:
        recs = (await self.db.execute(select(SapInboundRecord).where(
            SapInboundRecord.company_id == empresa.id, SapInboundRecord.source_system == SAP_SOURCE,
            SapInboundRecord.object_type == objeto.value, SapInboundRecord.source_key.like(f"{SAP_CLIENT}|{ebeln}%")))).scalars().all()
        for rec in recs:
            if rec.validation_status == V_VALID and rec.mapping_status == M_MAPPED:
                rec.promotion_status, rec.promoted_reference_id = P_PROMOTED, ref.id

    # ── lotes ────────────────────────────────────────────────────────────────

    async def lote(self, code: str, *, empresa: str, bu: str, farm: str, house: str, line: Optional[str], start_days: int,
                   area: Optional[str] = None, sex: str = "mixed", status: LotStatus = LotStatus.ACTIVE,
                   planned_close_days: Optional[int] = None, hatchery_purpose: Optional[str] = None, end_days: Optional[int] = None) -> Lot:
        emp = self.ctx.companies[empresa]
        lote = await self._uno(select(Lot).where(Lot.lot_code == code))
        if lote is None:
            linea = self.ctx.lines.get(line) if line else None
            curva = None
            if linea is not None:
                curva = await self._uno(select(GeneticWeightCurve).where(GeneticWeightCurve.genetic_line_id == linea.id,
                                                                         GeneticWeightCurve.is_active.is_(True)))
            lote = Lot(company_id=emp.id, farm_id=self.ctx.farms[farm].id, house_id=self.ctx.houses[house].id,
                       genetic_line_id=linea.id if linea else None, breed_id=self.ctx.breeds[line].id if line else None,
                       weight_curve_id=curva.id if curva else None, area_id=self.ctx.areas[area].id if area else None,
                       lot_code=code, bird_type=BirdTypeEnum(bu), sex=SexEnum(sex), status=status, activation_type="normal",
                       start_date=DT(start_days), hatchery_purpose=hatchery_purpose,
                       planned_close_date=DT(-planned_close_days) if planned_close_days is not None else None,
                       end_date=DT(end_days) if end_days is not None else None,
                       origin="NATIVE", source_system=MARKER, source_reference=self.ctx.run_id)
            self.db.add(lote); await self.db.flush(); self.c.marcar("lots", "created")
        else:
            self.c.marcar("lots", "existing")
        self.ctx.lots[code] = lote
        return lote

    async def apertura_manual(self, lote: Lot, *, fase: str, machos: int, hembras: int, edad: int, mort_m: int = 0, mort_f: int = 0,
                              feed_kg: Optional[float] = None, peso_g: Optional[float] = None, huevos: Optional[int] = None,
                              a_incubadora: Optional[int] = None, actor: str = "qa.admin") -> None:
        from app.lots.schemas import OpeningBalanceCreate
        from app.lots.service import LotService

        if await self._uno(select(OpeningBalance).where(OpeningBalance.lot_id == lote.id)) is not None:
            self.c.marcar("opening_balances", "existing"); return
        empresa = await self._uno(select(Company).where(Company.id == lote.company_id))
        datos = OpeningBalanceCreate(
            lot_id=lote.id, activation_date=lote.start_date.date(), phase_at_activation_id=self.ctx.fases[fase], age_days=edad,
            initial_male_count=machos, initial_female_count=hembras, accumulated_mortality_male=mort_m, accumulated_mortality_female=mort_f,
            accumulated_feed_kg=feed_kg, current_avg_weight=peso_g, accumulated_egg_production=huevos, accumulated_eggs_to_hatchery=a_incubadora,
            activation_reason=f"{MARKER}: lote existente antes de la implantación (dataset QA)",
            support_document_url="https://qa.globalavicola.com/soporte/apertura.pdf")
        ob = await LotService(self.db, self.actor(actor, empresa)).activate_manual(datos)
        if feed_kg is None:
            ob.feed_status = "UNKNOWN"
        if peso_g is None:
            ob.weight_status = "UNKNOWN"
        if huevos is None:
            ob.egg_production_status = "UNKNOWN" if fase == "PROD" else "NOT_APPLICABLE"
        if a_incubadora is None:
            ob.eggs_to_hatchery_status = "UNKNOWN" if fase == "PROD" else "NOT_APPLICABLE"
        await self.db.flush()
        self.c.marcar("opening_balances", "created")

    async def fase_de_lote(self, lote: Lot, fase: str, inicio_dias: int, machos: int, hembras: int) -> None:
        from app.lots.models import LotPhase

        existente = await self._uno(select(LotPhase).where(LotPhase.lot_id == lote.id, LotPhase.phase_id == self.ctx.fases[fase]))
        if existente is None:
            self.db.add(LotPhase(lot_id=lote.id, phase_id=self.ctx.fases[fase], start_date=D(inicio_dias),
                                 start_population_male=machos, start_population_female=hembras, is_active=True))
            await self.db.flush(); self.c.marcar("lot_phases", "created")
        else:
            self.c.marcar("lot_phases", "existing")

    async def cerrar_lote(self, lote: Lot, dias: int, *, actor: str = "qa.admin") -> None:
        """Cierre por el servicio real (BR-05 pesaje+alimento, R7 todo aprobado); la fecha se retrotrae al histórico."""
        from app.lots.service import LotService, _fecha_de_negocio

        if lote.status == LotStatus.CLOSED or lote.status == "closed":
            self.c.marcar("lots_closed", "existing"); return
        empresa = await self._uno(select(Company).where(Company.id == lote.company_id))
        await LotService(self.db, self.actor(actor, empresa)).close_lot(lote.id)
        lote.end_date = _fecha_de_negocio(D(dias))
        await self.db.flush()
        self.c.marcar("lots_closed", "created")

    # ── eventos ──────────────────────────────────────────────────────────────

    async def evento(self, actor_username: str, lote: Optional[Lot], tipo: str, dias: int, clave: str, *, empresa: Optional[str] = None,
                     aprobar: bool = True, **campos) -> OperationalEvent:
        """Crea el evento por el servicio real (validadores incluidos) con idempotencia determinista."""
        from app.operations.service import OperationsService

        emp = self.ctx.companies[empresa] if empresa else (await self._uno(select(Company).where(Company.id == lote.company_id)) if lote else None)
        actor = self.actor(actor_username, emp)
        key = f"{MARKER}:{emp.id}:{clave}"
        existente = await self._uno(select(OperationalEvent).where(OperationalEvent.idempotency_key == key,
                                                                   OperationalEvent.company_id == emp.id))
        if existente is not None:
            self.c.marcar("operational_events", "existing"); self.ctx.eventos[clave] = existente; return existente
        extra = dict(campos.pop("extra_data", None) or {})
        extra.update(qa_marker=MARKER, qa_run_id=self.ctx.run_id, qa_key=clave)
        datos = op_schemas.OperationalEventCreate(
            lot_id=lote.id if lote else None, event_type=tipo, event_date=D(dias), idempotency_key=key,
            observations=campos.pop("observations", None) or f"[{MARKER}] {clave}",
            farm_id=campos.pop("farm_id", lote.farm_id if lote else None), house_id=campos.pop("house_id", lote.house_id if lote else None),
            extra_data=extra, **campos)
        evento = await OperationsService(self.db, actor).create_event(datos)
        self.c.marcar("operational_events", "created")
        self.ctx.eventos[clave] = evento
        if aprobar:
            await self.aprobar_rapido(evento)
        return evento

    async def aprobar_rapido(self, evento: OperationalEvent) -> None:
        """`QA_HISTORY_FASTPATH`: historia ya revisada y aprobada (estado + acción + auditoría)."""
        if evento.status != EventStatus.REGISTERED:
            return
        sup, apr = self.ctx.users["qa.supervisor"], self.ctx.users["qa.approver"]
        if evento.company_id != sup.company_id:  # empresa de aislamiento: su propio supervisor aprueba (1 nivel)
            sup = apr = self.ctx.users["qa.isolation"]
        evento.status = EventStatus.APPROVED
        evento.reviewed_by_id, evento.approved_by_id = sup.id, apr.id
        self.db.add(review_models.ApprovalAction(event_id=evento.id, user_id=apr.id, action_type=review_models.ActionType.APPROVED,
                                                 observations=f"{MARKER} QA_HISTORY_FASTPATH"))
        await self.db.flush()
        actor = self.actor(apr.username)
        await audit_state_transition(self.db, evento, actor, "registered", "approved", comments=f"{MARKER} QA_HISTORY_FASTPATH")

    # ── workflow real ────────────────────────────────────────────────────────

    async def flujo(self, evento: OperationalEvent, destino: str, *, operador: str, observacion: str = "") -> OperationalEvent:
        """Lleva un evento REGISTERED al estado objetivo por los servicios reales (idempotente por estado)."""
        from app.operations.service import OperationsService
        from app.review.service import ApprovalService, ReviewService

        emp = await self._uno(select(Company).where(Company.id == evento.company_id))
        if evento.status.value == destino:
            return evento
        if destino == "draft":
            if evento.status == EventStatus.REGISTERED:
                evento.status = EventStatus.DRAFT; await self.db.flush()
            return evento
        if evento.status != EventStatus.REGISTERED:
            return evento  # ya recorrió el flujo en una ejecución previa
        ops = OperationsService(self.db, self.actor(operador, emp))
        try:
            await ops.submit_to_review(evento.id)
        except Exception as e:  # noqa: BLE001 — contexto para el diagnóstico del seed
            from app.business_units.service import unidades_de_alcance_productivo
            lote = await self._uno(select(Lot).where(Lot.id == evento.lot_id))
            unidades = await unidades_de_alcance_productivo(self.db, current_user=self.actor(operador, emp), company_id=emp.id)
            raise RuntimeError(f"flujo→{destino}: evento={evento.id} tipo={evento.event_type.value} lote={lote.lot_code if lote else evento.lot_id} "
                               f"bu={lote.bird_type if lote else None} empresa_lote={lote.company_id if lote else None} empresa_evento={evento.company_id} "
                               f"estado={evento.status.value} operador={operador} unidades={unidades}: {e!r}") from e
        if destino == "pending_review":
            return evento
        rev = ReviewService(self.db, self.actor("qa.supervisor", emp))
        await rev.start_review(evento.id)
        if destino == "in_review":
            return evento
        if destino == "returned":
            await rev.return_to_operator(evento.id, observacion or f"{MARKER}: falta el detalle; corrija y reenvíe")
            return evento
        await rev.complete_review(evento.id, observacion or None)
        if destino == "corrected":
            return evento
        apr = ApprovalService(self.db, self.actor("qa.approver", emp))
        if destino == "approved":
            await apr.approve(evento.id, observacion or None)
        elif destino == "rejected":
            await apr.reject(evento.id, observacion or f"{MARKER}: cantidad no coincide con el parte diario")
        return evento

    async def corregir(self, evento: OperationalEvent, *, corrector: str, campo: str, valor: str, motivo: str) -> None:
        from app.corrections.schemas import CorrectionCreate
        from app.corrections.service import CorrectionService

        if evento.status not in (EventStatus.REGISTERED, EventStatus.PENDING_REVIEW, EventStatus.IN_REVIEW, EventStatus.RETURNED, EventStatus.REJECTED):
            return
        emp = await self._uno(select(Company).where(Company.id == evento.company_id))
        tipo = self.ctx.catalogs.get(f"correction_type:{emp.id}:1")
        await CorrectionService(self.db, self.actor(corrector, emp)).create_correction(CorrectionCreate(
            event_id=evento.id, field_name=campo, original_value=str(getattr(evento, campo)), corrected_value=valor,
            correction_type_id=tipo.id if tipo else None, reason=motivo))

    async def reversar(self, evento: OperationalEvent, *, solicitante: str, motivo: str, aprobar_con: str) -> None:
        from app.operations.models import Reversal
        from app.reversals.schemas import ReversalCreate
        from app.reversals.service import ReversalService
        from app.review.service import ApprovalService, ReviewService

        if evento.status != EventStatus.APPROVED:
            return
        emp = await self._uno(select(Company).where(Company.id == evento.company_id))
        existente = await self._uno(select(Reversal).where(Reversal.original_event_id == evento.id))
        if existente is not None:
            # `R1`: reanudar por estado de la contrapartida en vez de abandonar — un `--apply` interrumpido
            # a mitad del flujo de reverso se completa, y uno ya terminado no se reintenta.
            await self._reanudar_reverso(existente, emp, aprobar_con, solicitante)
            return
        reverso = await ReversalService(self.db, self.actor(solicitante, emp)).solicitar(ReversalCreate(event_id=evento.id, reason=motivo))
        self.c.marcar("reversals", "created")
        await self._reanudar_reverso(reverso, emp, aprobar_con, solicitante)

    async def _reanudar_reverso(self, reverso, emp, aprobar_con: str, solicitante: str) -> None:
        """Completa los pasos que falten del reverso según el estado de la contrapartida (idempotente)."""
        from app.review.service import ApprovalService, ReviewService

        contrapartida = await self._uno(select(OperationalEvent).where(OperationalEvent.id == reverso.reversal_event_id))
        if contrapartida is None or contrapartida.status in (EventStatus.APPROVED, EventStatus.REVERSED):
            return  # ya efectivo (el reverso terminado deja ambos eventos en `reversed`)
        if not aprobar_con:
            return
        if contrapartida.status == EventStatus.PENDING_REVIEW:
            await ReviewService(self.db, self.actor("qa.supervisor", emp)).start_review(contrapartida.id)
        if contrapartida.status == EventStatus.IN_REVIEW:
            await ReviewService(self.db, self.actor("qa.supervisor", emp)).complete_review(
                contrapartida.id, f"{MARKER}: revisión de contrapartida")
        if contrapartida.status in (EventStatus.CORRECTED, EventStatus.REGISTERED):
            await ApprovalService(self.db, self.actor(aprobar_con, emp)).approve(contrapartida.id, f"{MARKER}: reverso aprobado")

    async def notificar(self, *, empresa: str, destinatario: str, tipo: str, payload: dict, ocurrencia: str, leida: bool,
                        entidad: Optional[str] = None, entidad_id: Optional[int] = None) -> None:
        from app.notifications.service import crear_notificacion

        emp = self.ctx.companies[empresa]
        u = self.ctx.users[destinatario]
        existente = await self._uno(select(Notification).where(Notification.company_id == emp.id, Notification.recipient_user_id == u.id,
                                                              Notification.notification_type == tipo,
                                                              Notification.payload["qa_key"].astext == ocurrencia))
        if existente is not None:
            self.c.marcar("notifications", "existing"); return
        aviso = await crear_notificacion(self.db, company_id=emp.id, recipient_user_id=u.id, notification_type=tipo,
                                         payload={**payload, "qa_marker": MARKER, "qa_key": ocurrencia},
                                         related_entity_type=entidad, related_entity_id=entidad_id, ocurrencia=ocurrencia)
        if aviso is not None and leida:
            aviso.read_at = datetime.now(timezone.utc)
        await self.db.flush()
        self.c.marcar("notifications", "created")

    # ── cutover (SPEC 006) ──────────────────────────────────────────────────

    async def cutover_aplicado(self, bu: str, filas: list[dict], *, dias_corte: int = 10) -> None:
        from app.cutover.models import CutoverBatch, CutoverBatchStatus
        from app.cutover.schemas import CutoverBatchCreate
        from app.cutover.service import CutoverService

        m = self.ctx.companies["MAIN"]
        referencia = f"QA-CUT-{bu.upper()}"
        batch = await self._uno(select(CutoverBatch).where(CutoverBatch.company_id == m.id, CutoverBatch.source_reference == referencia))
        if batch is not None and batch.status == CutoverBatchStatus.APPLIED.value:
            self.c.marcar("cutover_batches", "existing"); return
        sup = CutoverService(self.db, self.actor("qa.supervisor", m))
        creado = batch is None
        if creado:
            batch = await sup.crear_batch(CutoverBatchCreate(business_unit=bu, cutover_datetime=DT(dias_corte), source_system=MARKER,
                                                             source_reference=referencia, observations=f"{MARKER} carga de ejemplo aplicada"))
            self.c.marcar("cutover_batches", "created")
        if batch.status == CutoverBatchStatus.REJECTED.value:
            # `rejected` es terminal en el servicio: no hay reanudación posible sin un batch nuevo.
            self.c.marcar("cutover_batches", "skipped"); return
        # `R1`: reanudar por estado del batch en lugar de re-subir a ciegas (el apply es terminal).
        if batch.status in (CutoverBatchStatus.DRAFT.value, CutoverBatchStatus.VALIDATING.value, CutoverBatchStatus.VALIDATED.value):
            contenido = self.xlsx_cutover(bu, filas, company_id=m.id, cutover=DT(dias_corte))
            batch = await sup.subir_y_validar(batch.id, f"QA_cutover_{bu}_demo.xlsx", contenido)
            if batch.status != CutoverBatchStatus.VALIDATED.value:
                errores = await sup.validacion(batch.id)
                raise RuntimeError(f"cutover demo {bu} con errores: {errores['errors'][:3]}")
        if batch.status == CutoverBatchStatus.VALIDATED.value:
            await sup.enviar_a_aprobacion(batch.id)
        if batch.status == CutoverBatchStatus.PENDING_APPROVAL.value:
            await CutoverService(self.db, self.actor("qa.approver", m)).aprobar(batch.id)
        if batch.status == CutoverBatchStatus.APPROVED.value:
            await CutoverService(self.db, self.actor("qa.supervisor", m)).aplicar(batch.id)
        if not creado:
            self.c.marcar("cutover_batches", "updated")

    @staticmethod
    def xlsx_cutover(bu: str, filas: list[dict], *, company_id: Optional[int], cutover: Optional[datetime]) -> bytes:
        from openpyxl import load_workbook

        from app.cutover.contracts import contrato
        from app.cutover.templates import construir_plantilla_xlsx

        c = contrato(bu)
        libro = load_workbook(io.BytesIO(construir_plantilla_xlsx(c, company_id=company_id or 0, catalogo=[], cutover_datetime=cutover)))
        if company_id is None:  # fixture portable: la empresa la fija la sesión que la sube
            for fila in libro["Meta"].iter_rows():
                if fila[0].value == "company":
                    fila[1].value = ""
        hoja = libro["Datos"]
        for f in filas:
            hoja.append([f.get(col) for col in c.columns])
        buf = io.BytesIO()
        libro.save(buf)
        return buf.getvalue()
