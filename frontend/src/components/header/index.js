import React from "react";
import styled from "styled-components";

const Title = styled.h1`
  text-align: center;
  margin-top: 0;
  margin-bottom: 0;
`;

const Logo = styled.img`
width: 30%`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 16px;
`;

export default ({metadata}) =>
  metadata['image_url'] || process.env.REACT_APP_NAME ? (
    <Header>
      {metadata['image_url'] ? (
        <a href={metadata['image_link']}>
        <Logo
          src={metadata['image_url']}
          alt={process.env.REACT_APP_NAME}
          
        /></a>
      ) : (
        <Title>{process.env.REACT_APP_NAME}</Title>
      )}
    </Header>
  ) : null;
