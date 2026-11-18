import { useEffect, useMemo, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip as MapTooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const palette = ['#4967d5', '#12a98c', '#ef9a36', '#9570dc', '#e06d8e', '#43a4c7', '#90a83a', '#d66c42'];
const number = (value) => Number(value || 0).toLocaleString('en-IN');
const tidy = (value) => String(value || '').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());

async function loadDashboard(signal) {
  const [summaryResponse, categoriesResponse, listingsResponse] = await Promise.all([
    fetch('/api/dashboard/summary', { signal }),
    fetch('/api/dashboard/categories', { signal }),
    fetch('/api/listings?limit=1000', { signal }),
  ]);
  for (const response of [summaryResponse, categoriesResponse, listingsResponse]) {
    if (!response.ok) throw new Error(`API request failed (${response.status})`);
  }
  const [summary, categories, listings] = await Promise.all([
    summaryResponse.json(), categoriesResponse.json(), listingsResponse.json(),
  ]);
  return { summary, categories, listings };
}

function analyzeRows(rows) {
  const names = new Map();
  const sourceIds = new Set();
  const postcodes = new Map();
  let repeatedNameRows = 0;
  let duplicateSourceIds = 0;
  let postcodeRows = 0;
  for (const row of rows) {
    const normalizedName = String(row.business_name || '').trim().toLocaleLowerCase();
    if (names.has(normalizedName)) repeatedNameRows += 1;
    names.set(normalizedName, (names.get(normalizedName) || 0) + 1);
    const id = `${row.source}:${row.source_id}`;
    if (sourceIds.has(id)) duplicateSourceIds += 1;
    sourceIds.add(id);
    const match = String(row.address || '').match(/\b(\d{3})\s?(\d{3})\b/);
    if (match) {
      postcodeRows += 1;
      const postcode = `${match[1]}${match[2]}`;
      postcodes.set(postcode, (postcodes.get(postcode) || 0) + 1);
    }
  }
  const categoryRows = new Map();
  for (const row of rows) {
    const category = row.category || 'unknown';
    const item = categoryRows.get(category) || { label: tidy(category), total: 0, withPhone: 0 };
    item.total += 1;
    if (row.phone) item.withPhone += 1;
    categoryRows.set(category, item);
  }
  const categoryCoverage = [...categoryRows.values()].map((row) => ({
    ...row,
    coverage: row.total ? (row.withPhone / row.total) * 100 : 0,
  })).sort((a, b) => b.total - a.total);
  return {
    phoneCount: rows.filter((row) => row.phone).length,
    coordinateCount: rows.filter((row) => row.latitude !== null && row.latitude !== '' && row.longitude !== null && row.longitude !== '' && Number.isFinite(Number(row.latitude)) && Number.isFinite(Number(row.longitude))).length,
    postcodeRows,
    postcodes: [...postcodes].map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count),
    repeatedNameRows,
    duplicateSourceIds,
    unspecifiedCategory: rows.filter((row) => String(row.category).toLowerCase() === 'yes').length,
    categoryCoverage,
  };
}

function Metric({ label, value, note, icon }) {
  return <div className="metric panel"><div className="metric-top"><span>{label}</span><span className="metric-icon">{icon}</span></div><strong>{value}</strong><small>{note}</small></div>;
}

function CategoryChart({ rows, total }) {
  const top = rows.slice(0, 10).map((row) => ({ ...row, share: total ? (row.count / total) * 100 : 0 }));
  return <section className="panel chart-panel chart-panel-wide">
    <div className="panel-heading"><div><h2>Category mix</h2><p>Top 10 categories · percentages are of all listings</p></div><span className="panel-dot" style={{ background: '#ef9a36' }} /></div>
    <div className="chart-area category-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={top} layout="vertical" margin={{ top: 5, right: 42, bottom: 4, left: 12 }}>
      <CartesianGrid stroke="#edf0f5" strokeDasharray="3 5" horizontal={false} /><XAxis type="number" hide /><YAxis type="category" dataKey="label" width={158} axisLine={false} tickLine={false} tick={{ fill: '#536078', fontSize: 11 }} />
      <Tooltip cursor={{ fill: '#f4f6fb' }} contentStyle={{ border: '1px solid #e8ebf1', borderRadius: 10 }} formatter={(value, _name, item) => [`${number(value)} · ${item.payload.share.toFixed(1)}%`, 'Listings']} />
      <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={25} label={{ position: 'right', fill: '#68748a', fontSize: 10, formatter: (value) => `${value}` }}>{top.map((row, index) => <Cell key={row.label} fill={palette[index % palette.length]} />)}</Bar>
    </BarChart></ResponsiveContainer></div>
    <div className="category-insights">{rows.slice(0, 3).map((row) => <span key={row.label}><b>{tidy(row.label)}</b> {number(row.count)} · {total ? ((row.count / total) * 100).toFixed(1) : '0.0'}%</span>)}</div>
  </section>;
}

function PhoneChart({ rows, total }) {
  const top = [...rows].sort((a, b) => b.total - a.total).slice(0, 10);
  return <section className="panel chart-panel">
    <div className="panel-heading"><div><h2>Phone coverage by category</h2><p>Share with a phone number in the {number(total)} listing sample</p></div><span className="panel-dot" style={{ background: '#12a98c' }} /></div>
    {top.length ? <div className="chart-area"><ResponsiveContainer width="100%" height="100%"><BarChart data={top} layout="vertical" margin={{ top: 3, right: 32, bottom: 3, left: 5 }}>
      <CartesianGrid stroke="#edf0f5" strokeDasharray="3 5" horizontal={false} /><XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} axisLine={false} tickLine={false} tick={{ fill: '#8a94a6', fontSize: 10 }} /><YAxis type="category" dataKey="label" width={105} axisLine={false} tickLine={false} tick={{ fill: '#536078', fontSize: 10 }} />
      <Tooltip contentStyle={{ border: '1px solid #e8ebf1', borderRadius: 10 }} formatter={(value, _name, item) => [`${item.payload.withPhone}/${item.payload.total} · ${Number(value).toFixed(1)}%`, 'Phone listed']} />
      <Bar dataKey="coverage" radius={[0, 6, 6, 0]} maxBarSize={19} fill="#12a98c" />
    </BarChart></ResponsiveContainer></div> : <div className="chart-empty">No phone coverage data available.</div>}
  </section>;
}

function PostcodeChart({ rows, matched, total }) {
  const top = rows.slice(0, 8);
  return <section className="panel chart-panel">
    <div className="panel-heading"><div><h2>Listings by postcode</h2><p>{number(matched)} of {number(total)} addresses include a six-digit postcode</p></div><span className="panel-dot" style={{ background: '#9570dc' }} /></div>
    {top.length ? <div className="chart-area"><ResponsiveContainer width="100%" height="100%"><BarChart data={top} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
      <CartesianGrid stroke="#edf0f5" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#768197', fontSize: 10 }} /><YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: '#8a94a6', fontSize: 10 }} width={28} /><Tooltip formatter={(value) => [`${value} listings`, 'Postcode']} contentStyle={{ border: '1px solid #e8ebf1', borderRadius: 10 }} /><Bar dataKey="count" fill="#9570dc" radius={[5, 5, 0, 0]} maxBarSize={32} />
    </BarChart></ResponsiveContainer></div> : <div className="chart-empty">No postcodes were found in the loaded addresses.</div>}
  </section>;
}

function ListingsMap({ rows }) {
  const points = rows.filter((row) => row.latitude !== null && row.latitude !== '' && row.longitude !== null && row.longitude !== '' && Number.isFinite(Number(row.latitude)) && Number.isFinite(Number(row.longitude)));
  const bounds = points.length ? points.map((row) => [Number(row.latitude), Number(row.longitude)]) : undefined;
  return <section className="panel map-panel">
    <div className="panel-heading"><div><h2>Listing locations</h2><p>Each dot is a source-preserved listing · select a dot for details</p></div><span className="map-count">{number(points.length)} mapped</span></div>
    <div className="map-frame">{points.length ? <MapContainer key={points.length} bounds={bounds} boundsOptions={{ padding: [28, 28] }} scrollWheelZoom={false}>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {points.map((row) => <CircleMarker key={`${row.source}:${row.source_id}`} center={[Number(row.latitude), Number(row.longitude)]} radius={5} pathOptions={{ color: '#fff', weight: 1, fillColor: '#4967d5', fillOpacity: 0.76 }}>
        <MapTooltip>{row.business_name}</MapTooltip><Popup><div className="map-popup"><b>{row.business_name}</b><span>{tidy(row.category)}</span><small>{row.address || 'Address not listed'}</small>{row.phone && <a href={`tel:${row.phone}`}>{row.phone}</a>}<small>Source ID: {row.source_id}</small></div></Popup>
      </CircleMarker>)}
    </MapContainer> : <div className="map-empty">No coordinates available.</div>}</div>
  </section>;
}

function QualityPanel({ analysis, total }) {
  return <section className="panel quality-panel"><div className="panel-heading"><div><h2>Data quality checks</h2><p>Review these caveats before interpreting the charts</p></div><span className="quality-mark">i</span></div>
    <div className="quality-grid">
      <div><b>{number(analysis.repeatedNameRows)}</b><span>repeated-name rows</span><small>Branches are kept separate by source ID.</small></div>
      <div><b>{number(analysis.duplicateSourceIds)}</b><span>duplicate source IDs</span><small>Identity key is source + source ID.</small></div>
      <div><b>{number(analysis.unspecifiedCategory)}</b><span>“yes” categories</span><small>Likely unspecified tags; left unchanged.</small></div>
      <div><b>{number(total - analysis.postcodeRows)}</b><span>addresses without postcode</span><small>Postcode chart uses only extracted values.</small></div>
    </div>
  </section>;
}

function ListingsTable({ rows }) {
  return <section className="panel table-panel"><div className="panel-heading table-heading"><div><h2>Business listings</h2><p>Source-linked sample with contact details where available</p></div><span className="table-count">{number(rows.length)} loaded</span></div>
    <div className="table-scroll"><table><thead><tr><th>Business</th><th>Category</th><th>Address</th><th>Phone</th><th>Source</th><th>Source ID</th></tr></thead><tbody>
      {rows.slice(0, 30).map((row) => <tr key={`${row.source}:${row.source_id}`}><td className="business-cell">{row.business_name}</td><td><span className="category-pill">{tidy(row.category)}</span></td><td className="address-cell">{row.address || <span className="missing-value">Not listed</span>}</td><td>{row.phone ? <a className="phone-link" href={`tel:${row.phone}`}>{row.phone}</a> : <span className="missing-value">Not listed</span>}</td><td><a className="source-link" href={row.source_url} target="_blank" rel="noreferrer">{row.source} ↗</a></td><td>{row.source_id}</td></tr>)}
    </tbody></table><div className="table-note">Showing the first 30 rows. All {number(rows.length)} loaded records are used in the dashboard analysis.</div></div>
  </section>;
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    loadDashboard(controller.signal).then(setData).catch((err) => { if (err.name !== 'AbortError') setError(err.message || 'Could not load dashboard data.'); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);
  const analysis = useMemo(() => analyzeRows(data?.listings || []), [data]);
  if (loading) return <main className="screen-state"><div className="loader" /><p>Loading Bengaluru listings…</p></main>;
  if (error) return <main className="screen-state"><div className="state-icon">!</div><h1>Dashboard unavailable</h1><p>{error}. Start MySQL and the FastAPI service, then refresh.</p><button onClick={() => window.location.reload()}>Try again</button></main>;
  const total = data.listings.length;
  const phonePercent = total ? (analysis.phoneCount / total) * 100 : 0;
  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#top" aria-label="Bengaluru business dashboard home"><span className="brand-mark"><span /><span /><span /></span><span>Local<span className="brand-accent">scope</span></span></a><div className="topbar-right"><span className="live-dot" /> API connected <span className="topbar-divider" /><span className="city-tag">Bengaluru, IN</span></div></header>
    <main id="top" className="main-content">
      <section className="hero"><div className="hero-copy"><div className="eyebrow"><span /> BUSINESS INTELLIGENCE</div><h1>Know your<br /><em>local landscape.</em></h1><p>Explore source-linked Bengaluru business listings through category mix, location, and data quality.</p><div className="hero-meta"><span className="meta-icon">⌖</span><span>Bengaluru, India</span><span className="meta-sep">·</span><span>{number(total)} listings analyzed</span></div></div><div className="hero-card"><div className="hero-card-top"><span className="hero-card-label">PHONE COVERAGE</span><span className="hero-card-icon">↗</span></div><strong>{phonePercent.toFixed(1)}%</strong><p>{number(analysis.phoneCount)} of {number(total)} listings have a phone</p><div className="hero-card-rule" /><div className="hero-card-bottom"><span>Directory</span><b>OpenStreetMap</b></div></div><div className="hero-orb orb-one" /><div className="hero-orb orb-two" /></section>
      <section className="metrics-grid" aria-label="Dashboard summary"><Metric label="Total listings" value={number(total)} note="Source-linked records" icon="▦" /><Metric label="Categories" value={number(data.summary.categories)} note="Distinct business tags" icon="◈" /><Metric label="With phone" value={`${number(analysis.phoneCount)} · ${phonePercent.toFixed(1)}%`} note="Small contact-number sample" icon="☎" /><Metric label="With coordinates" value={number(analysis.coordinateCount)} note="Plotted on the map" icon="⌖" /></section>
      {total < 500 && <div className="coverage-notice"><span className="coverage-notice-icon">i</span><div><b>Dataset is below the assignment target</b><p>{number(total)} listings loaded. The assignment requests 500+ records; document the current collection limit and data source clearly.</p></div></div>}
      <div className="section-title-row"><div><div className="section-kicker">THE BREAKDOWN</div><h2>Category and contact patterns</h2></div><span className="coverage-chip">{number(data.summary.categories)} categories</span></div>
      <section className="charts-grid"><CategoryChart rows={data.categories} total={total} /><PhoneChart rows={analysis.categoryCoverage} total={total} /><PostcodeChart rows={analysis.postcodes} matched={analysis.postcodeRows} total={total} /></section>
      <ListingsMap rows={data.listings} />
      <QualityPanel analysis={analysis} total={total} />
      <ListingsTable rows={data.listings} />
      <footer className="footer"><div><b>Local<span className="brand-accent">scope</span></b><span> · Bengaluru business listings</span></div><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors</a><span>Business listing details link to their source records.</span></footer>
    </main>
  </div>;
}
