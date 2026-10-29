export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#060c10", color: "#e6f0f5" }}>{children}</body></html>);
}
