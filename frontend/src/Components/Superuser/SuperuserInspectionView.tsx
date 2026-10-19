// AA TaxSystem
import OwnerManagePage from "@/Pages/Manage/OwnerManagePage";

interface SuperuserInspectionViewProps {
  ownerId: number;
  ownerType: string;
  onBack: () => void;
}

export function SuperuserInspectionView({
  ownerId,
  onBack,
}: SuperuserInspectionViewProps) {
  return <OwnerManagePage ownerIdOverride={ownerId} onBack={onBack} />;
}

export default SuperuserInspectionView;
