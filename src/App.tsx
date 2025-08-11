import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useAccount } from 'wagmi';

export default function App() {
  const { address, chain } = useAccount();
  return (
    <div style={{ padding: 24, color: 'white', background: '#0c1222', minHeight: '100vh' }}>
      <h1>🔒 ToshLock + RainbowKit</h1>
      <ConnectButton />
      {address && (
        <p style={{ marginTop: 12 }}>
          Connected: {address.slice(0,6)}…{address.slice(-4)} on chain {chain?.id}
        </p>
      )}
    </div>
  );
}
