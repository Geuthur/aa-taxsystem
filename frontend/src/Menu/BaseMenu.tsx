// React
import { Link, useLocation } from "react-router-dom";

// Third Party
import { ShieldAlert } from "lucide-react";
import { Nav } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";

export type MenuLinkItem = components["schemas"]["MenuLink"];

export interface MenuCategory {
  name: string;
  link?: string;
  links?: MenuLinkItem[];
}

export interface MenuProps {
  isLoading: boolean;
  data: Array<MenuCategory | MenuLinkItem>;
  error: boolean;
}

export interface ToPath {
    toPath: (link: string) => string;
}

export const SuperuserMenuItem = ({ link, toPath }: { link: MenuLinkItem } & ToPath) => {
    const { t } = useTranslation();
    const path = useLocation();
    const hit = path.pathname.includes("/superuser/");

    return (
        <Nav.Item as="li">
            <Nav.Link
                as={Link}
                to={{ pathname: toPath(link.link ?? ""), search: path.search }}
                id={link.name}
                key={link.name}
                active={hit}
                className="aa-nav-danger d-flex align-items-center gap-1"
            >
                <ShieldAlert size={14} className="text-danger" />
                <span className="text-danger">{t(link.name)}</span>
            </Nav.Link>
        </Nav.Item>
    );
};

export const MenuItem = ({ link, toPath }: { link: MenuLinkItem } & ToPath) => {
    const { t } = useTranslation();
    const path = useLocation();
    const hit = path.pathname.endsWith(link.link ?? "");
    const isExternal = Boolean(
        link.is_external ||
        link.link?.startsWith("http://") ||
        link.link?.startsWith("https://")
    );

    if (link.link === "/superuser/" || link.name.toLowerCase() === "superuser") {
        return <SuperuserMenuItem link={link} toPath={toPath} />;
    }

    if (isExternal) {
        return (
            <Nav.Item as="li">
                <Nav.Link
                    href={link.link ?? "#"}
                    id={link.name}
                    key={link.name}
                >
                    {t(link.name)}
                </Nav.Link>
            </Nav.Item>
        );
    }

    return (
        <Nav.Item as="li">
            <Nav.Link
                as={Link}
                to={{ pathname: toPath(link.link ?? ""), search: path.search }}
                id={link.name}
                key={link.name}
                active={hit}
            >
                {t(link.name)}
            </Nav.Link>
        </Nav.Item>
    );
};
