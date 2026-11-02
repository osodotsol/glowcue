const ngn = new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 });

export const formatPrice = (amount: number) => ngn.format(amount);

export const formatDelta = (amount: number) =>
  amount === 0 ? "same price" : `${amount > 0 ? "+" : "−"}${ngn.format(Math.abs(amount))}`;
