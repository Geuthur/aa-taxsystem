// React
import { Link } from "react-router-dom";

// Third Party
import { useTranslation } from "react-i18next";

// AA TaxSystem
import BaseSectionHeader from "@/Components/Base/BaseHeader";

function MainPage() {
  const { t } = useTranslation();

  return (
    <main>
      <BaseSectionHeader />
      <section className="mt-3 aa-panel">
        <div className="d-flex align-items-center justify-content-between gap-3">
          <span>{t("Example Content")}</span>
          <Link className="aa-btn aa-btn-sm" to="styleguide/">
            {t("Style Guide")}
          </Link>
        </div>
      </section>
    </main>
  );
}

export default MainPage;
