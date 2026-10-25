// AA TaxSystem
import OwnerManagePage from "@/Pages/OwnerManagePage";

interface AdministrationInspectionViewProps {
  ownerId: number;
  ownerType: string;
  onBack: () => void;
}

export function AdministrationInspectionView({
  ownerId,
  onBack,
}: AdministrationInspectionViewProps) {
  return <OwnerManagePage ownerIdOverride={ownerId} onBack={onBack} />;
}

export default AdministrationInspectionView;
