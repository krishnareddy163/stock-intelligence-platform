export type PeriodKey = '1D' | '1W' | '1M' | '3M' | '1Y' | '5Y';

export interface ShareholdingQuarter {
  quarter: string;
  promoters: number;
  fii: number;
  dii: number;
  retail: number;
  others: number;
}

export interface Stock {
  symbol: string;
  name: string;
  sector: string;
  exchange: string;
  currentPrice: number;
  previousClose: number;
  open: number;
  high52w: number;
  low52w: number;
  marketCap: number;
  peRatio: number;
  pbRatio: number;
  dividendYield: number;
  beta: number;
  eps: number;
  roe: number;
  debtToEquity: number;
  about: string;
  priceHistory: Record<PeriodKey, number[]>;
  shareholding: ShareholdingQuarter[];
}

function gen(base: number, length: number, volatility: number): number[] {
  const arr: number[] = [base];
  for (let i = 1; i < length; i++) {
    const delta = (Math.random() - 0.48) * volatility;
    arr.push(Math.max(1, +(arr[i - 1] + delta).toFixed(2)));
  }
  return arr;
}

function shareholdingHistory(
  promoters: number, fii: number, dii: number, retail: number
): ShareholdingQuarter[] {
  const quarters = ['Q1 FY22','Q2 FY22','Q3 FY22','Q4 FY22','Q1 FY23','Q2 FY23','Q3 FY23','Q4 FY23','Q1 FY24','Q2 FY24','Q3 FY24','Q4 FY24'];
  return quarters.map((q, i) => {
    const drift = (i - 5) * 0.05;
    const p = +(promoters + drift * 0.3).toFixed(2);
    const f = +(fii - drift * 0.15 + (Math.random() - 0.5) * 0.4).toFixed(2);
    const d = +(dii + drift * 0.1 + (Math.random() - 0.5) * 0.2).toFixed(2);
    const r = +(100 - p - f - d).toFixed(2);
    return { quarter: q, promoters: p, fii: f, dii: d, retail: r, others: 0 };
  });
}

export const STOCKS: Stock[] = [
  {
    symbol: 'RELIANCE',
    name: 'Reliance Industries',
    sector: 'Oil & Gas',
    exchange: 'NSE',
    currentPrice: 2847.35,
    previousClose: 2820.10,
    open: 2825.00,
    high52w: 3217.90,
    low52w: 2220.30,
    marketCap: 1924500,
    peRatio: 27.4,
    pbRatio: 2.1,
    dividendYield: 0.31,
    beta: 0.92,
    eps: 103.9,
    roe: 8.7,
    debtToEquity: 0.38,
    about: 'Reliance Industries Limited is an Indian multinational conglomerate with interests in energy, petrochemicals, natural gas, retail, telecommunications, mass media, and textiles.',
    priceHistory: {
      '1D': gen(2820, 78, 8),
      '1W': gen(2750, 7, 30),
      '1M': gen(2620, 30, 40),
      '3M': gen(2500, 90, 35),
      '1Y': gen(2200, 252, 30),
      '5Y': gen(1100, 260, 50),
    },
    shareholding: shareholdingHistory(50.30, 21.04, 16.80, 11.86),
  },
  {
    symbol: 'TCS',
    name: 'Tata Consultancy Services',
    sector: 'IT',
    exchange: 'NSE',
    currentPrice: 3912.50,
    previousClose: 3875.20,
    open: 3880.00,
    high52w: 4255.00,
    low52w: 3311.80,
    marketCap: 1418700,
    peRatio: 31.2,
    pbRatio: 13.5,
    dividendYield: 1.51,
    beta: 0.78,
    eps: 125.4,
    roe: 46.5,
    debtToEquity: 0.04,
    about: 'Tata Consultancy Services is an Indian multinational information technology services and consulting company headquartered in Mumbai. It is part of the Tata Group.',
    priceHistory: {
      '1D': gen(3875, 78, 12),
      '1W': gen(3800, 7, 45),
      '1M': gen(3650, 30, 55),
      '3M': gen(3400, 90, 50),
      '1Y': gen(3300, 252, 45),
      '5Y': gen(2100, 260, 80),
    },
    shareholding: shareholdingHistory(72.30, 12.04, 7.80, 7.86),
  },
  {
    symbol: 'HDFCBANK',
    name: 'HDFC Bank',
    sector: 'Banking',
    exchange: 'NSE',
    currentPrice: 1621.45,
    previousClose: 1605.80,
    open: 1608.00,
    high52w: 1794.00,
    low52w: 1363.55,
    marketCap: 1237600,
    peRatio: 18.7,
    pbRatio: 2.4,
    dividendYield: 1.10,
    beta: 0.95,
    eps: 86.7,
    roe: 16.8,
    debtToEquity: 7.2,
    about: 'HDFC Bank Limited is an Indian banking and financial services company headquartered in Mumbai. It is India\'s largest private sector bank by assets.',
    priceHistory: {
      '1D': gen(1605, 78, 5),
      '1W': gen(1570, 7, 18),
      '1M': gen(1490, 30, 22),
      '3M': gen(1380, 90, 20),
      '1Y': gen(1370, 252, 18),
      '5Y': gen(1000, 260, 25),
    },
    shareholding: shareholdingHistory(0, 54.74, 22.32, 22.94),
  },
  {
    symbol: 'INFY',
    name: 'Infosys',
    sector: 'IT',
    exchange: 'NSE',
    currentPrice: 1847.20,
    previousClose: 1831.45,
    open: 1835.00,
    high52w: 1953.90,
    low52w: 1358.35,
    marketCap: 768400,
    peRatio: 26.4,
    pbRatio: 7.8,
    dividendYield: 2.42,
    beta: 0.82,
    eps: 69.97,
    roe: 31.9,
    debtToEquity: 0.07,
    about: 'Infosys Limited is an Indian multinational IT company that offers business consulting, information technology, and outsourcing services.',
    priceHistory: {
      '1D': gen(1831, 78, 6),
      '1W': gen(1790, 7, 22),
      '1M': gen(1700, 30, 30),
      '3M': gen(1550, 90, 28),
      '1Y': gen(1360, 252, 25),
      '5Y': gen(800, 260, 40),
    },
    shareholding: shareholdingHistory(14.97, 33.48, 19.80, 31.75),
  },
  {
    symbol: 'ICICIBANK',
    name: 'ICICI Bank',
    sector: 'Banking',
    exchange: 'NSE',
    currentPrice: 1231.80,
    previousClose: 1218.60,
    open: 1220.00,
    high52w: 1338.75,
    low52w: 988.20,
    marketCap: 868200,
    peRatio: 17.9,
    pbRatio: 2.9,
    dividendYield: 0.81,
    beta: 1.08,
    eps: 68.82,
    roe: 17.2,
    debtToEquity: 6.8,
    about: 'ICICI Bank Limited is an Indian multinational bank and financial services company headquartered in Mumbai with its registered office in Vadodara.',
    priceHistory: {
      '1D': gen(1218, 78, 4),
      '1W': gen(1190, 7, 15),
      '1M': gen(1130, 30, 18),
      '3M': gen(1020, 90, 16),
      '1Y': gen(990, 252, 14),
      '5Y': gen(500, 260, 22),
    },
    shareholding: shareholdingHistory(0, 47.32, 24.18, 28.50),
  },
  {
    symbol: 'WIPRO',
    name: 'Wipro',
    sector: 'IT',
    exchange: 'NSE',
    currentPrice: 482.15,
    previousClose: 476.90,
    open: 478.00,
    high52w: 567.20,
    low52w: 380.75,
    marketCap: 251200,
    peRatio: 22.1,
    pbRatio: 3.4,
    dividendYield: 0.21,
    beta: 0.85,
    eps: 21.82,
    roe: 15.6,
    debtToEquity: 0.15,
    about: 'Wipro Limited is an Indian multinational corporation that provides information technology, consulting and business process services.',
    priceHistory: {
      '1D': gen(476, 78, 2),
      '1W': gen(462, 7, 8),
      '1M': gen(430, 30, 10),
      '3M': gen(390, 90, 9),
      '1Y': gen(385, 252, 8),
      '5Y': gen(210, 260, 12),
    },
    shareholding: shareholdingHistory(72.93, 7.04, 5.30, 14.73),
  },
  {
    symbol: 'SBIN',
    name: 'State Bank of India',
    sector: 'Banking',
    exchange: 'NSE',
    currentPrice: 812.35,
    previousClose: 802.45,
    open: 805.00,
    high52w: 912.10,
    low52w: 600.65,
    marketCap: 725400,
    peRatio: 10.8,
    pbRatio: 1.7,
    dividendYield: 1.72,
    beta: 1.22,
    eps: 75.22,
    roe: 18.4,
    debtToEquity: 12.5,
    about: 'State Bank of India is an Indian multinational public sector bank and financial services company headquartered in Mumbai. It is a government-owned corporation.',
    priceHistory: {
      '1D': gen(802, 78, 3),
      '1W': gen(785, 7, 12),
      '1M': gen(745, 30, 15),
      '3M': gen(680, 90, 13),
      '1Y': gen(605, 252, 11),
      '5Y': gen(280, 260, 18),
    },
    shareholding: shareholdingHistory(57.50, 11.90, 20.40, 10.20),
  },
  {
    symbol: 'BAJFINANCE',
    name: 'Bajaj Finance',
    sector: 'NBFC',
    exchange: 'NSE',
    currentPrice: 7241.80,
    previousClose: 7168.20,
    open: 7180.00,
    high52w: 8192.00,
    low52w: 6187.80,
    marketCap: 438100,
    peRatio: 35.7,
    pbRatio: 6.2,
    dividendYield: 0.28,
    beta: 1.31,
    eps: 202.74,
    roe: 19.4,
    debtToEquity: 4.1,
    about: 'Bajaj Finance Limited is an Indian non-banking financial company headquartered in Pune. It accepts deposits and provides loans and other financial products.',
    priceHistory: {
      '1D': gen(7168, 78, 25),
      '1W': gen(6980, 7, 80),
      '1M': gen(6600, 30, 90),
      '3M': gen(6200, 90, 75),
      '1Y': gen(6190, 252, 70),
      '5Y': gen(2800, 260, 150),
    },
    shareholding: shareholdingHistory(54.78, 22.14, 12.30, 10.78),
  },
  {
    symbol: 'MARUTI',
    name: 'Maruti Suzuki',
    sector: 'Auto',
    exchange: 'NSE',
    currentPrice: 12847.60,
    previousClose: 12690.40,
    open: 12700.00,
    high52w: 13680.00,
    low52w: 9575.80,
    marketCap: 400200,
    peRatio: 29.3,
    pbRatio: 5.1,
    dividendYield: 0.78,
    beta: 0.88,
    eps: 438.16,
    roe: 18.2,
    debtToEquity: 0.01,
    about: 'Maruti Suzuki India Limited is a subsidiary of Suzuki Motor Corporation and is India\'s largest passenger vehicle manufacturer.',
    priceHistory: {
      '1D': gen(12690, 78, 45),
      '1W': gen(12300, 7, 150),
      '1M': gen(11500, 30, 180),
      '3M': gen(10500, 90, 160),
      '1Y': gen(9580, 252, 140),
      '5Y': gen(6000, 260, 200),
    },
    shareholding: shareholdingHistory(58.19, 18.82, 13.40, 9.59),
  },
  {
    symbol: 'TATAMOTORS',
    name: 'Tata Motors',
    sector: 'Auto',
    exchange: 'NSE',
    currentPrice: 1024.30,
    previousClose: 1008.75,
    open: 1012.00,
    high52w: 1179.00,
    low52w: 748.50,
    marketCap: 371400,
    peRatio: 13.2,
    pbRatio: 3.8,
    dividendYield: 0.20,
    beta: 1.45,
    eps: 77.60,
    roe: 32.1,
    debtToEquity: 1.82,
    about: 'Tata Motors Limited is an Indian multinational automotive company and member of the Tata Group. It manufactures cars, trucks, vans, coaches, buses, luxury cars, sports cars, and construction equipment.',
    priceHistory: {
      '1D': gen(1008, 78, 4),
      '1W': gen(975, 7, 20),
      '1M': gen(900, 30, 22),
      '3M': gen(780, 90, 20),
      '1Y': gen(750, 252, 18),
      '5Y': gen(180, 260, 30),
    },
    shareholding: shareholdingHistory(46.39, 18.84, 19.10, 15.67),
  },
  {
    symbol: 'SUNPHARMA',
    name: 'Sun Pharmaceutical',
    sector: 'Pharma',
    exchange: 'NSE',
    currentPrice: 1678.90,
    previousClose: 1658.30,
    open: 1662.00,
    high52w: 1960.25,
    low52w: 1310.65,
    marketCap: 402800,
    peRatio: 38.4,
    pbRatio: 5.7,
    dividendYield: 0.60,
    beta: 0.72,
    eps: 43.72,
    roe: 15.3,
    debtToEquity: 0.18,
    about: 'Sun Pharmaceutical Industries Limited is an Indian multinational pharmaceutical company headquartered in Mumbai. It is the largest pharmaceutical company in India.',
    priceHistory: {
      '1D': gen(1658, 78, 6),
      '1W': gen(1620, 7, 22),
      '1M': gen(1530, 30, 25),
      '3M': gen(1370, 90, 22),
      '1Y': gen(1315, 252, 20),
      '5Y': gen(650, 260, 35),
    },
    shareholding: shareholdingHistory(54.48, 14.24, 18.80, 12.48),
  },
  {
    symbol: 'ASIANPAINT',
    name: 'Asian Paints',
    sector: 'Consumer',
    exchange: 'NSE',
    currentPrice: 2842.55,
    previousClose: 2809.20,
    open: 2815.00,
    high52w: 3394.85,
    low52w: 2274.35,
    marketCap: 272400,
    peRatio: 54.2,
    pbRatio: 16.8,
    dividendYield: 1.05,
    beta: 0.68,
    eps: 52.44,
    roe: 31.5,
    debtToEquity: 0.10,
    about: 'Asian Paints Limited is an Indian multinational paint company headquartered in Mumbai. It manufactures, sells and distributes paints, coatings, home decor products, bath fittings and related services.',
    priceHistory: {
      '1D': gen(2809, 78, 10),
      '1W': gen(2730, 7, 35),
      '1M': gen(2580, 30, 40),
      '3M': gen(2400, 90, 38),
      '1Y': gen(2280, 252, 35),
      '5Y': gen(1400, 260, 55),
    },
    shareholding: shareholdingHistory(52.63, 17.24, 16.80, 13.33),
  },
];

export const INDICES = [
  { name: 'NIFTY 50',    value: '24,162.20', change: '+138.50', pct: '+0.58%', up: true },
  { name: 'SENSEX',      value: '79,486.32', change: '+444.96', pct: '+0.56%', up: true },
  { name: 'NIFTY Bank',  value: '52,478.75', change: '-124.30', pct: '-0.24%', up: false },
  { name: 'NIFTY IT',    value: '38,924.60', change: '+312.45', pct: '+0.81%', up: true },
  { name: 'NIFTY Auto',  value: '22,847.15', change: '+205.60', pct: '+0.91%', up: true },
  { name: 'NIFTY Pharma',value: '20,314.85', change: '-89.40',  pct: '-0.44%', up: false },
];

export const SECTORS = [
  { name: 'IT',       change: '+1.2%', up: true,  count: 42 },
  { name: 'Banking',  change: '-0.3%', up: false, count: 38 },
  { name: 'Auto',     change: '+0.9%', up: true,  count: 24 },
  { name: 'Pharma',   change: '-0.5%', up: false, count: 31 },
  { name: 'FMCG',     change: '+0.4%', up: true,  count: 19 },
  { name: 'Metals',   change: '+1.8%', up: true,  count: 27 },
  { name: 'Energy',   change: '+0.2%', up: true,  count: 18 },
  { name: 'Realty',   change: '-1.1%', up: false, count: 15 },
];

export const TOP_GAINERS = STOCKS
  .map(s => ({ ...s, change: s.currentPrice - s.previousClose, pct: ((s.currentPrice - s.previousClose) / s.previousClose) * 100 }))
  .sort((a, b) => b.pct - a.pct)
  .slice(0, 5);

export const TOP_LOSERS = STOCKS
  .map(s => ({ ...s, change: s.currentPrice - s.previousClose, pct: ((s.currentPrice - s.previousClose) / s.previousClose) * 100 }))
  .sort((a, b) => a.pct - b.pct)
  .slice(0, 5);
