// React
import type { ReactNode } from 'react';

// Third Party
import { Card } from 'react-bootstrap';

export interface BaseSectionHeaderProps {
    name?: string;
    children?: ReactNode;
}

function BaseSectionHeader({ name = "Header", children }: BaseSectionHeaderProps) {
    return (
        <Card aria-labelledby="session-heading">
            <Card.Header className="bg-primary rounded d-flex flex-wrap justify-content-between align-items-center gap-2">
                <h3 id="session-heading" className="mb-0">{name}</h3>
                {children && <div className="text-end d-flex flex-wrap align-items-center gap-2">{children}</div>}
            </Card.Header>
        </Card>
    );
};

export default BaseSectionHeader;
