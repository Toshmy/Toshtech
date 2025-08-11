import { defineChain } from 'viem';

export const pepuTestnet = defineChain({
  id: 97741,
  name: 'PEPU Testnet',
  nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
  rpcUrls: {
    default: { http: ['https://rpc-pepu-v2-testnet-vn4qxxp9og.t.conduit.xyz'] },
    public:  { http: ['https://rpc-pepu-v2-testnet-vn4qxxp9og.t.conduit.xyz'] },
  },
});
