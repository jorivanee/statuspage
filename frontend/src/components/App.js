import React, { useEffect } from "react";
import styled from "styled-components";
import Status from "./status";
import Header from "./header";
import Components from "./components";
import Incidents from "./incidents";
import Footer from "./footer";

const Container = styled.div`
  max-width: 1008px;
  padding: 16px;
  margin: 16px auto;
`;

const ComponentsContainer = styled.div`
  box-shadow: 0px 0px 33px -32px rgba(0, 0, 0, 0.75);
  border-radius: 3px;
  background-color: white;
  padding: 16px;
`;

export default function App () {
  const [loading, setLoading] = React.useState(true);
  const [status, setStatus] = React.useState({});
  const [error, setError] = React.useState("");
  useEffect(()=>{
    if(loading){
      update();
    }
  })
  const update = () => {
    fetch(`${process.env.REACT_APP_API_BASE_URL}/status/raw`).then((response)=>{return response.json();}).then((data)=>{
      setStatus(data);
      setLoading(false);
    }).catch((error)=>{
      setError("An unknown error occurred")
    })
  }
  return (
    <Container>
      <Header />
      <ComponentsContainer>
        <Status
          loading={loading}
          error={{
            hasError: error,
            errors: { error },
          }}
          status={status['status']}
          refetch={() => {
            update();
          }}
        />
        <Components
          loading={loading}
          components={status['components']}
        />
      </ComponentsContainer>
      <Incidents loading={loading} incidents={status['incidents']} />
      <Footer />
    </Container>
  );
};
