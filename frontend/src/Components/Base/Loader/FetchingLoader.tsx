// Third Party
import { useTranslation } from "react-i18next";

// AA TaxSystem
import styles from "@/Styles/modules/FetchingLoader.module.css";

interface LoaderProps {
  message?: string;
  className?: string;
}

export const FetchingLoader = ({ message, className = '' }: LoaderProps = {}) => {
  const { t } = useTranslation();

  return (
    <div className={`${styles['flex-container-loader']} ${className}`}>
      <div
        className={`spinner-border text-info ${styles["spinner"]}`}
        role="status"
      >
        <span className="visually-hidden">{t("Loading...")}</span>
      </div>
      {message && (
        <span>
          {message}
        </span>
      )}
    </div>
  );
};

export default FetchingLoader;
