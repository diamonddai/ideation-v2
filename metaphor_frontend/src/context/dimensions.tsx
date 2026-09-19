// context/dimensions.tsx
import React, { createContext, useContext, useState } from 'react';

interface DimensionsContextType {
  dimensions: string[];
  setDimensions: (dimensions: string[]) => void;
}

const DimensionsContext = createContext<DimensionsContextType>({
  dimensions: [],
  setDimensions: () => {}
});

export const DimensionsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [dimensions, setDimensions] = useState<string[]>([]);
  
  return (
    <DimensionsContext.Provider value={{ dimensions, setDimensions }}>
      {children}
    </DimensionsContext.Provider>
  );
};

export const useDimensions = () => useContext(DimensionsContext);