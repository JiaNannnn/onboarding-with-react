import React, { ReactNode } from 'react';
import './Footer.css';

/**
 * Footer component props interface
 */
export interface FooterProps {
  /**
   * Copyright text
   */
  copyright?: string;
  
  /**
   * Logo or brand component
   */
  logo?: ReactNode;
  
  /**
   * Navigation links
   */
  links?: Array<{
    /**
     * Link ID
     */
    id: string;
    
    /**
     * Link label
     */
    label: string;
    
    /**
     * Link URL
     */
    href?: string;
    
    /**
     * Click handler
     */
    onClick?: () => void;
  }>;
  
  /**
   * Social media icons/links
   */
  socialLinks?: ReactNode;
  
  /**
   * Additional content to display in the footer
   */
  children?: ReactNode;
  
  /**
   * Footer variant
   */
  variant?: 'default' | 'minimal' | 'dark' | 'colored';
  
  /**
   * Custom background color
   */
  backgroundColor?: string;
  
  /**
   * Custom text color
   */
  textColor?: string;
  
  /**
   * Whether to include additional legal links
   */
  showLegalLinks?: boolean;
  
  /**
   * Legal links to display
   */
  legalLinks?: Array<{
    /**
     * Link ID
     */
    id: string;
    
    /**
     * Link label
     */
    label: string;
    
    /**
     * Link URL
     */
    href?: string;
    
    /**
     * Click handler
     */
    onClick?: () => void;
  }>;
  
  /**
   * Additional CSS class name
   */
  className?: string;
  
  /**
   * Whether the footer is fixed at the bottom of the page
   */
  fixed?: boolean;
  
  /**
   * Whether to display a top border
   */
  showBorder?: boolean;
  
  /**
   * Footer layout
   */
  layout?: 'default' | 'centered' | 'split';
  
  /**
   * ID for testing purposes
   */
  id?: string;
}

/**
 * Footer component
 * 
 * Application footer that typically contains copyright info, links, and branding
 */
const Footer: React.FC<FooterProps> = ({
  copyright = `© ${new Date().getFullYear()} BMS to EnOS Onboarding Tool`,
  logo,
  links = [],
  socialLinks,
  children,
  variant = 'default',
  backgroundColor,
  textColor,
  showLegalLinks = true,
  legalLinks = [
    { id: 'privacy', label: 'Privacy Policy' },
    { id: 'terms', label: 'Terms of Service' },
    { id: 'cookies', label: 'Cookie Policy' },
  ],
  className = '',
  fixed = false,
  showBorder = true,
  layout = 'default',
  id,
}) => {
  // Combine class names
  const footerClasses = [
    'bms-footer',
    `bms-footer--${variant}`,
    `bms-footer--${layout}`,
    fixed ? 'bms-footer--fixed' : '',
    showBorder ? 'bms-footer--bordered' : '',
    className,
  ].filter(Boolean).join(' ');
  
  // Apply custom styles
  const footerStyle = {
    backgroundColor,
    color: textColor,
  };
  
  return (
    <footer className={footerClasses} style={footerStyle} id={id}>
      <div className="bms-footer__content">
        <div className="bms-footer__main">
          {/* Logo and copyright section */}
          <div className="bms-footer__brand">
            {logo && <div className="bms-footer__logo">{logo}</div>}
            {copyright && <div className="bms-footer__copyright">{copyright}</div>}
          </div>
          
          {/* Navigation links */}
          {links.length > 0 && (
            <nav className="bms-footer__nav">
              <ul className="bms-footer__links">
                {links.map(link => (
                  <li key={link.id} className="bms-footer__link-item">
                    {link.href ? (
                      <a 
                        href={link.href} 
                        className="bms-footer__link"
                        onClick={link.onClick}
                      >
                        {link.label}
                      </a>
                    ) : (
                      <button 
                        className="bms-footer__link bms-footer__link--button"
                        onClick={link.onClick}
                      >
                        {link.label}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </nav>
          )}
          
          {/* Social media links */}
          {socialLinks && (
            <div className="bms-footer__social">
              {socialLinks}
            </div>
          )}
        </div>
        
        {/* Custom content */}
        {children && (
          <div className="bms-footer__custom">
            {children}
          </div>
        )}
        
        {/* Legal links */}
        {showLegalLinks && legalLinks.length > 0 && (
          <div className="bms-footer__legal">
            <ul className="bms-footer__legal-links">
              {legalLinks.map(link => (
                <li key={link.id} className="bms-footer__legal-item">
                  {link.href ? (
                    <a 
                      href={link.href} 
                      className="bms-footer__legal-link"
                      onClick={link.onClick}
                    >
                      {link.label}
                    </a>
                  ) : (
                    <button 
                      className="bms-footer__legal-link bms-footer__legal-link--button"
                      onClick={link.onClick}
                    >
                      {link.label}
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </footer>
  );
};

export default Footer; 