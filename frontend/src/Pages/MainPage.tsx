// React
import { Link } from "react-router";

// Third Party
import { Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import BaseSectionHeader from "@/Components/Base/BaseHeader";

function MainPage() {
  const { t } = useTranslation();

  return (
    <Card className="border-0 bg-transparent">
      <BaseSectionHeader />
      <Card className="mt-3 aa-panel">
        <Card.Body className="p-0">
          <div className="d-flex align-items-center justify-content-between gap-3">
            <span>{t("Example Content")}</span>
            <Link className="aa-btn aa-btn-sm" to="styleguide/">
              {t("Style Guide")}
            </Link>
          </div>
        </Card.Body>
      </Card>
    </Card>
  );
}

export default MainPage;
