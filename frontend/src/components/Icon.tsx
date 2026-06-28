import {
 Home, ClipboardList, FileText, BarChart3, Search, CheckCircle,
 Shield, RefreshCw, Users, Bird, Package, Truck, ArrowUpRight,
 Wheat, Scale, Skull, Trash2, Syringe, Pill, Building2,
 Egg, Baby, Lock, Plane, ZoomIn, ChevronLeft, Check,
 Undo2, X, Pencil, ArrowDownRight, Flame, Lightbulb, TrendingUp,
 MapPin, Info, FolderOpen, Star, Settings, Circle,
 Activity, AlertTriangle, Eye, Plus, Database, Upload,
 Download, Wrench, UserCog, Gauge, Microscope, Thermometer,
 type LucideIcon,
} from 'lucide-react'

const iconMap: Record<string, LucideIcon> = {
 home: Home,
 dashboard: BarChart3,
 operations: FileText,
 masters: Database,
 review: Search,
 approvals: CheckCircle,
 reports: TrendingUp,
 audit: Shield,
 sap: RefreshCw,
 users: Users,
 settings: Settings,
 bird: Bird,
 package: Package,
 truck: Truck,
 arrowUp: ArrowUpRight,
 wheat: Wheat,
 scale: Scale,
 skull: Skull,
 trash: Trash2,
 syringe: Syringe,
 pill: Pill,
 building: Building2,
 egg: Egg,
 baby: Baby,
 lock: Lock,
 plane: Plane,
 zoom: ZoomIn,
 chevronLeft: ChevronLeft,
 check: Check,
 undo: Undo2,
 xCircle: X,
 pencil: Pencil,
 arrowDown: ArrowDownRight,
 flame: Flame,
 lightbulb: Lightbulb,
 trendingUp: TrendingUp,
 mapPin: MapPin,
 info: Info,
 folder: FolderOpen,
 star: Star,
 settingsGear: Settings,
 circle: Circle,
 activity: Activity,
 alertTriangle: AlertTriangle,
 eye: Eye,
 plus: Plus,
 database: Database,
 upload: Upload,
 download: Download,
 wrench: Wrench,
 userCog: UserCog,
 gauge: Gauge,
 microscope: Microscope,
 thermometer: Thermometer,
 clipboard: ClipboardList,
}

// Event type to icon mapping
export const EVENT_ICONS: Record<string, LucideIcon> = {
 bird_reception: Bird,
 bird_distribution: Package,
 bird_transfer: Truck,
 bird_exit: ArrowUpRight,
 feed_registration: Wheat,
 weight_recording: Scale,
 mortality_recording: Skull,
 cull_recording: Trash2,
 vaccination: Syringe,
 medication: Pill,
 farm_inspection: Building2,
 transport_inspection: Truck,
 hatchery_inspection: Thermometer,
 egg_collection: Egg,
 egg_classification: ClipboardList,
 egg_dispatch: ArrowUpRight,
 egg_reception_hatchery: ArrowDownRight,
 incubation_load: Flame,
 ovoscopy: Eye,
 transfer_to_hatcher: RefreshCw,
 birth_registration: Baby,
 chick_dispatch: Truck,
 lot_closure: Lock,
 grandparent_import: Plane,
}

interface IconProps {
 name: string
 size?: number
 className?: string
}

export default function Icon({ name, size = 20, className = '' }: IconProps) {
 const LucideIcon = iconMap[name]
 if (!LucideIcon) return null
 return <LucideIcon size={size} className={className} />
}

export { iconMap }
