import React from "react";
import styled from "styled-components";
import Status from "./status";
import statuses from "./statuses";

const Component = styled.div`
  background-color: #f7f8f9;
  padding: 8px 16px;
  border-radius: 3px;
  justify-content: space-between;
  align-items: center;
  display: flex;

  :not(:last-child) {
    margin-bottom: 8px;
  }
`;

export default ({ component }) => {
  var status = statuses[component.status.status];
  status['name'] = component.status.name;
  return (
    <Component>
      {component.name} <Status status={status} />
    </Component>
  );
};
