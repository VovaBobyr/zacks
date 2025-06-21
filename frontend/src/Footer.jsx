import React from 'react';
import './Footer.css';
import { FaFacebookF, FaTwitter, FaGooglePlusG, FaPinterestP, FaInstagram, FaRss } from 'react-icons/fa';

const Footer = () => {
  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="copyright">
          Copyright 2025 &copy; Bobyr&copy;
        </div>
        <div className="social-links">
          <a href="#" aria-label="Facebook"><FaFacebookF /></a>
          <a href="#" aria-label="Twitter"><FaTwitter /></a>
          <a href="#" aria-label="Google Plus"><FaGooglePlusG /></a>
          <a href="#" aria-label="Pinterest"><FaPinterestP /></a>
          <a href="#" aria-label="Instagram"><FaInstagram /></a>
          <a href="#" aria-label="RSS"><FaRss /></a>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 