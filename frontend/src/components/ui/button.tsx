import type {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  ReactNode,
} from 'react';

export type ButtonVariant = 'default' | 'outline' | 'secondary' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({
  variant = 'default',
  className = '',
  type = 'button',
  ...props
}: ButtonProps): JSX.Element {
  const classes = ['shadcn-btn', `shadcn-btn-${variant}`, className]
    .filter(Boolean)
    .join(' ');

  return <button type={type} className={classes} {...props} />;
}

interface ButtonLinkProps
  extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href' | 'children' | 'className'> {
  href: string;
  variant?: ButtonVariant;
  className?: string;
  children: ReactNode;
}

export function ButtonLink({
  href,
  variant = 'outline',
  className = '',
  children,
  ...props
}: ButtonLinkProps): JSX.Element {
  const classes = ['shadcn-btn', `shadcn-btn-${variant}`, 'shadcn-btn-link', className]
    .filter(Boolean)
    .join(' ');

  return (
    <a href={href} className={classes} {...props}>
      {children}
    </a>
  );
}
