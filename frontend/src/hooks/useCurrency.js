import { useMarket } from "../context/MarketContext";
import { CURRENCIES, EXCHANGE_RATES } from "../markets";

/**
 * Convert an amount (minor units, e.g. kopiykas) from one currency to another.
 * All conversions go through UAH as the base currency.
 */
export function convertAmount(amountMinor, fromCurrency, toCurrency, rates = EXCHANGE_RATES) {
  if (fromCurrency === toCurrency || !amountMinor) return amountMinor;
  const fromRate = rates[fromCurrency] ?? 1;
  const toRate = rates[toCurrency] ?? 1;
  // minor → major → UAH → target major
  return (amountMinor / 100) * (fromRate / toRate);
}

/**
 * Format a major-unit amount (already converted) as a locale-aware currency string.
 */
export function formatCurrency(amount, currencyCode, locale) {
  const meta = CURRENCIES[currencyCode];
  const decimals = meta?.decimals ?? 2;
  try {
    return new Intl.NumberFormat(locale || "en", {
      style: "currency",
      currency: currencyCode,
      minimumFractionDigits: 0,
      maximumFractionDigits: decimals,
    }).format(amount);
  } catch {
    return `${meta?.symbol ?? ""}${amount.toFixed(decimals)}`;
  }
}

/**
 * Hook — returns a `format(price)` function that converts and formats a price
 * according to the current market/currency/locale preferences.
 *
 * price: { amount: number (minor units), currency: string } | number | null
 */
export function useCurrency() {
  const { currency, market, exchangeRates } = useMarket();

  function format(price) {
    if (price === null || price === undefined) return "—";
    const raw = typeof price === "object" ? price?.amount : price;
    const fromCurrency = (typeof price === "object" ? price?.currency : null) ?? "UAH";
    const amount = typeof raw === "number" ? raw : Number(raw);
    if (Number.isNaN(amount) || amount <= 0) return "—";

    const converted = convertAmount(amount, fromCurrency, currency, exchangeRates);
    return formatCurrency(converted, currency, market.locale);
  }

  return { format, currency, locale: market.locale };
}
