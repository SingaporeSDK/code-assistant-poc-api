import { createContext } from "react";
import React, { useState } from "react";

const UserInformationContext = createContext();

const UserInformationProvider = ({ children }) => {
  const userInformation = {
    name: "John Doe",
    email: "john.doe@example.com"
  };

  const [count, setCount] = useState();
  let countObject = {
    count: count,
    setCount: setCount
  };
  userInformation.countObject = countObject;

  return (
    <UserInformationContext.Provider value={userInformation}>
      {children}
    </UserInformationContext.Provider>
  );
};

export { UserInformationContext, UserInformationProvider }; 
// This context can be used to share user information across components