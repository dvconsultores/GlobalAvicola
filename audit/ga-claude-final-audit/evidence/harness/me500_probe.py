"""Sonda de auditoría (no producto): reproduce el 500 de GET /me con la fixture de R-188
y captura la traza real (ASGITransport con raise_app_exceptions=True). Limpia lo que crea."""
import asyncio, os, uuid, traceback
from sqlalchemy import select, text, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


async def main():
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password, create_access_token
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit, UserBusinessUnit
    from app.masters.models import Company
    from app.audit.models import AuditLog
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    motor = create_async_engine(os.environ["DATABASE_URL"])
    P = "BU188PROBE-"
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{P}A-{uuid.uuid4().hex[:6]}", is_active=True); s.add(a); await s.flush()
        unidad = (await s.execute(select(BusinessUnit).where(BusinessUnit.code == "broiler"))).scalar_one()
        s.add(CompanyBusinessUnit(company_id=a.id, business_unit_id=unidad.id, is_enabled=True)); await s.flush()
        r = Role(name=f"{P}OP-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True); s.add(r); await s.flush()
        s.add(Permission(role_id=r.id, module="reports", action=PermissionAction.READ, scope_type="company")); await s.flush()
        u = User(first_name="ZERO", last_name="Probe", email=f"{P}z-{uuid.uuid4().hex[:6]}@e.test",
                 username=f"{P}Z-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x"),
                 company_id=a.id, role_id=r.id, is_active=True)
        s.add(u); await s.commit(); uid, cid, rid = u.id, a.id, r.id
    tok = create_access_token(data={"sub": str(uid)})
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=True), base_url="http://test") as ac:
        try:
            resp = await ac.get("/api/v1/me", headers={"Authorization": f"Bearer {tok}"})
            print("STATUS", resp.status_code, resp.text[:600])
        except Exception:
            traceback.print_exc()
    async with motor.begin() as c:
        await c.execute(delete(AuditLog).where(AuditLog.user_id == uid))
        await c.execute(delete(UserBusinessUnit).where(UserBusinessUnit.user_id == uid))
        await c.execute(text("DELETE FROM permissions WHERE role_id=:r"), {"r": rid})
        await c.execute(text("DELETE FROM users WHERE id=:u"), {"u": uid})
        await c.execute(text("DELETE FROM roles WHERE id=:r"), {"r": rid})
        await c.execute(delete(CompanyBusinessUnit).where(CompanyBusinessUnit.company_id == cid))
        await c.execute(text("DELETE FROM companies WHERE id=:c"), {"c": cid})
    await motor.dispose()


asyncio.run(main())
