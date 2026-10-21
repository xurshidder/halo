// A creator's fit, 0-100, as a ring around the number. The top match gets the gold point
// at the end of its arc, cut free by a gap, as on the Collab logo.
export default function ScoreRing({ score, top = false, size = 56 }: { score: number; top?: boolean; size?: number }) {
  const stroke = size >= 56 ? 6 : 4;
  const r = (size - stroke) / 2 - (top ? stroke * 0.6 : 0);
  const c = size / 2;
  const length = 2 * Math.PI * r;
  const end = (score / 100) * 2 * Math.PI - Math.PI / 2;
  const px = c + r * Math.cos(end);
  const py = c + r * Math.sin(end);
  const point = stroke * 1.05;
  return (
    <svg className="score-ring" width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${score}/100`}>
      <circle className="track" cx={c} cy={c} r={r} strokeWidth={stroke} />
      <circle
        className="arc"
        cx={c}
        cy={c}
        r={r}
        strokeWidth={stroke}
        strokeDasharray={`${(length * score) / 100} ${length}`}
        transform={`rotate(-90 ${c} ${c})`}
      />
      {top && (
        <>
          <circle className="gap" cx={px} cy={py} r={point + stroke * 0.55} />
          <circle className="point" cx={px} cy={py} r={point} />
        </>
      )}
      <text className="num" x={c} y={c} textAnchor="middle" dominantBaseline="central" fontSize={size * 0.31}>
        {score}
      </text>
    </svg>
  );
}
