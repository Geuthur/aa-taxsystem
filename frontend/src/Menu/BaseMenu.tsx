// React
import { Link, useLocation } from "react-router-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { ShieldAlert } from "lucide-react";
import { Nav } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { loadSettingsOwners } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";

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

export const AdministrationMenuItem = ({ link, toPath }: { link: MenuLinkItem } & ToPath) => {
    const { t } = useTranslation();
    const path = useLocation();
    const hit = path.pathname.includes("/administration/");

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

export const SettingsMenuItem = ({ link, toPath }: { link: MenuLinkItem } & ToPath) => {
    const { t } = useTranslation();
    const path = useLocation();
    const hit = path.pathname.endsWith(link.link ?? "");

    const { data: owners } = useQuery({
        queryKey: queryKeys.SettingsOwners,
        queryFn: () => loadSettingsOwners(),
        refetchInterval: 30000,
        staleTime: 15000,
    });

    const issueCount = (owners ?? []).filter((o) => (o.status || "").toLowerCase() !== "ok").length;
    const badgeCount = Math.max(issueCount, link.badge ?? 0);
    const hasStatusIssue = Boolean(link.has_errors || issueCount > 0);

    return (
        <Nav.Item as="li">
            <Nav.Link
                as={Link}
                to={{ pathname: toPath(link.link ?? ""), search: path.search }}
                id={link.name}
                key={link.name}
                active={hit}
                data-testid="settings-nav-link"
            >
                {t(link.name)}
                {badgeCount > 0 ? (
                    <span className={`badge bg-danger ms-1 ${hasStatusIssue ? "aa-menu-badge-pulse" : ""}`}>
                        {badgeCount}
                    </span>
                ) : null}
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

    if (link.link === "/administration/" || link.name.toLowerCase() === "administration") {
        return <AdministrationMenuItem link={link} toPath={toPath} />;
    }

    if (link.link === "/settings/" || link.name.toLowerCase() === "settings") {
        return <SettingsMenuItem link={link} toPath={toPath} />;
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
                className={link.has_errors ? "aa-order-nav-pulse" : ""}
            >
                {link.has_errors && (
                    <span className="aa-pending-dot-container me-1" aria-hidden="true">
                        <span className="aa-danger-dot-ping" />
                        <span className="aa-danger-dot-core" />
                    </span>
                )}
                {t(link.name)}
                {link.badge ? (
                    <span className="badge bg-danger ms-1">{link.badge}</span>
                ) : null}
            </Nav.Link>
        </Nav.Item>
    );
};

