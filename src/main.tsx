import React from 'react';
import ReactDOM from 'react-dom/client';
import '@rainbow-me/rainbowkit/styles.css';
import {
  RainbowKitProvider,
  darkTheme,
  getDefaultConfig,
} from '@rainbow-me/rainbowkit';
import { WagmiProvider } from 'wagmi';
import { http } from 'viem';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { pepuTestnet } from './chains';
import App from './App';

const projectId = '6e2df48125e4f633b093361ba0a87c81';

const wagmiConfig = getDefaultConfig({
  appName: 'ToshLock',
  projectId,
  chains: [pepuTestnet],
  transports: {
    [pepuTestnet.id]: http('https://rpc-pepu-v2-testnet-vn4qxxp9og.t.conduit.xyz'),
  },
});

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider chains={[pepuTestnet]} theme={darkTheme()}>
          <App />
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  </React.StrictMode>
);
