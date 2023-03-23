import React from "react";
import styled from "styled-components";
import statuses from "./statuses";

const StatusBar = styled.div`
  background-color: ${(props) =>
    props.backgroundColour ? props.backgroundColour : "#b1b1b1"};
  color: white;
  padding: 16px;
  border-radius: 3px;
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  transition: 0.3s;
`;

const Status = styled.h2`
  font-size: 20px;
  margin: 0;
  font-weight: normal;
`;

const Reload = styled.button`
  background-color: transparent;
  color: white;
  text-decoration: underline;
  border: none;
  cursor: pointer;
  text-align: right;
  padding: 0;
`;

const Code = styled.code`
  white-space: pre-wrap;
  display: block;
`;

export default ({ loading, error, status, refetch }) => {
  var st = {};
  if (!loading) { 
    st = statuses[status['status']];
   }

  return (
    <>
      {error.hasError && (
        <Code>
          <div>An error occured</div>
          {JSON.stringify(error.errors, null, 3)}
        </Code>
      )}
      <StatusBar backgroundColour={st?.backgroundColour}>
        <Status>{status?.text}</Status>
        <Reload onClick={refetch}>{loading ? "reloading" : status['timeago']}</Reload>
      </StatusBar>
    </>
  );
};
