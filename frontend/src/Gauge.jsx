// A scalable double-dial: outer arc = temperature, inner arc = usage.
// Drawn in a 200x200 viewBox so it scales crisply to any container size.
const START = -220; // degrees, sweeping clockwise to END (gap at the bottom)
const END = 40;
const CX = 100;
const CY = 100;
const R_OUTER = 84;
const R_INNER = 60;

function polar(angleDeg, radius) {
  const a = (angleDeg * Math.PI) / 180;
  return [CX + radius * Math.cos(a), CY + radius * Math.sin(a)];
}

function arcPath(radius) {
  const [x1, y1] = polar(START, radius);
  const [x2, y2] = polar(END, radius);
  const large = Math.abs(END - START) > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2}`;
}

// Green -> amber -> red based on fraction of the way to max.
function colorFor(frac) {
  if (frac < 0.6) return "#3ddc84";
  if (frac < 0.8) return "#ffd23f";
  return "#ff5252";
}

const SWEEP = ((END - START) * Math.PI) / 180;

function Ring({ radius, width, frac, color }) {
  const len = radius * SWEEP;
  return (
    <>
      <path d={arcPath(radius)} className="ring-track" strokeWidth={width} />
      <path
        d={arcPath(radius)}
        className="ring-fill"
        stroke={color}
        strokeWidth={width}
        strokeDasharray={len}
        strokeDashoffset={len * (1 - frac)}
      />
    </>
  );
}

export default function Gauge({ label, temp, tempMax, usage }) {
  const tFrac = Math.max(0, Math.min(1, temp / tempMax));
  const hasUsage = usage !== null && usage !== undefined;
  const uFrac = hasUsage ? Math.max(0, Math.min(1, usage / 100)) : 0;

  return (
    <div className="gauge">
      <svg viewBox="0 0 200 200" preserveAspectRatio="xMidYMid meet">
        <Ring radius={R_OUTER} width={13} frac={tFrac} color={colorFor(tFrac)} />
        {hasUsage && (
          <Ring radius={R_INNER} width={11} frac={uFrac} color={colorFor(uFrac)} />
        )}
        <text x={CX} y={95} className="dial-temp" fill={colorFor(tFrac)}>
          {Math.round(temp)}<tspan className="dial-unit">°</tspan>
        </text>
        <text x={CX} y={122} className="dial-usage">
          {hasUsage ? `${Math.round(usage)}% load` : "temp"}
        </text>
      </svg>
      <div className="gauge-label">{label}</div>
    </div>
  );
}
