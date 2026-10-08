/**
 * render a Link with given URL and text optional children
 * @param url The URL to link to
 * @param text The text to display for the link
 * @param children Optional React children to include inside the link
 * @param external Whether the link should open in a new tab (external link)
 * @returns A JSX element representing the link
 */
export const renderLink = ({
        url,
        text,
        children,
        external,
        className
    }: {url: string, text: string, children?: React.ReactNode, external?: boolean, className?: string}) => {
    return (
        <a href={url} className={`${className ?? ''}`} target={external ? '_blank' : undefined} rel={external ? 'noopener noreferrer' : undefined}>
            {text}
            {children}
        </a>
    );
};

