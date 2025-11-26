function TypingIndicator() {
  return (
    <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-white/10 bg-black/40 shadow-[0_0_20px_rgba(0,240,255,0.15)] backdrop-blur-md">
      <span className="text-[10px] uppercase tracking-[0.4em] text-kaiops-primary/80 animate-pulse">KaiOPS</span>
      <div className="flex items-center gap-1 h-3">
        {[0, 1, 2, 3, 4].map((bar) => (
          <div
            key={bar}
            className="w-1 bg-kaiops-primary/80 rounded-full animate-waveform"
            style={{ 
              animationDelay: `${bar * 0.1}s`,
              height: '100%'
            }}
          ></div>
        ))}
      </div>
    </div>
  )
}

export default TypingIndicator
