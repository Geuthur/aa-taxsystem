// React
import type { ReactNode } from "react";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";

export type ModalSchema = {
  modal_id: string;
  url: string;
  title?: ReactNode;
  text?: string;
  icon?: ReactNode;
  color?: string | null;
  buttonText?: string | null;
};

export type MenuSchema = components["schemas"]["MenuSchema"];
export type UserData = components["schemas"]["UserData"];
export type UserSettingsSchema = components["schemas"]["UserSettingsSchema"];
export type UserSettingsUpdateRequest = components["schemas"]["UserSettingsUpdateRequest"];
