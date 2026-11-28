// Keep normalization separate from routing so data-driven local extensions share it.
export const fold = (value: string) => value.toLocaleLowerCase('vi').replace(/đ/g, 'd')
  .normalize('NFD').replace(/\p{Mark}/gu, '').replace(/\s+/g, ' ').trim();

export function polite(message: string) {
  let text = fold(message).replace(/[.!?]+$/, '');
  for (let pass = 0; pass < 3; pass++) {
    text = text.replace(/^(?:astra(?: oi)?[, ]+|em oi[, ]+|(?:cho|giup|gium) (?:co|thay|toi|minh|tao|tui|em) |nho em |hay |vui long |lam on )/, '')
      .replace(/(?: (?:cho|giup|gium|ho)(?: (?:co|thay|toi|minh|tao|tui|em))?(?: voi)?| (?:di|nhe|nha|voi|em))$/, '');
  }
  return text;
}
