import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

type Theme = 'Nature' | 'Artifact' | 'Body' | 'Life' | 'Others' | null;
type Method = 'semantic' | 'functional' | 'perceptual' | 'structural' | null;
type Strategy = 'Guided' | 'Blinded' | '';

interface FilterContextType {
  selectedTheme: Theme;
  selectedMethod: Method;
  selectedStrategy: Strategy;
  setSelectedTheme: (theme: Theme) => void;
  setSelectedMethod: (method: Method) => void;
  setSelectedStrategy: (strategy: Strategy) => void;
  resetFilters: () => void;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [selectedTheme, setSelectedTheme] = useState<Theme>(null);
  const [selectedMethod, setSelectedMethod] = useState<Method>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy>('');

  const resetFilters = () => {
    setSelectedTheme(null);
    setSelectedMethod(null);
    setSelectedStrategy('');
  };

  return (
    <FilterContext.Provider value={{ 
      selectedTheme, 
      selectedMethod, 
      selectedStrategy,
      setSelectedTheme, 
      setSelectedMethod,
      setSelectedStrategy,
      resetFilters
    }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useFilter() {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error('useFilter must be used within a FilterProvider');
  }
  return context;
}