import React from "react";
import styled from "styled-components";

const Footer = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
`;

const Branding = styled.a`
  color: #6e6b6b;
  font-size: 13px;
  text-decoration: none;
  transition: 0.3s;
  display: block;

  :hover {
    opacity: 0.9;
  }
`;

export default () => (
  <Footer>
    <div></div>
    <Branding
      href="https://github.com/jorivanee/statuspage"
      rel="noopener"
      target="_blank"
    >
      {process.env.REACT_APP_FOOTER || "Powered by Jori van Ee's Status Page"}
      
    </Branding>
  </Footer>
);
