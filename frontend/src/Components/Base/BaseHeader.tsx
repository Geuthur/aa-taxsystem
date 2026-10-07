// React
import type { ReactNode } from 'react';

export interface BaseSectionHeaderProps {
    name?: string;
    children?: ReactNode;
}

function BaseSectionHeader({ name = "Header", children }: BaseSectionHeaderProps) {
    return (
        <section className="card" aria-labelledby="session-heading">
            <div className="card-header bg-primary rounded d-flex justify-content-between align-items-center">
                <h3 id="session-heading" className="mb-0">{name}</h3>
                {children && <div className="text-end d-flex align-items-center gap-2">{children}</div>}
            </div>
        </section>
    );
};

export default BaseSectionHeader;
