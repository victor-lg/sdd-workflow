// Terabytes a gigabytes, con 1 TB = 1024 GB.
export function tbAGb(tb) {
  if (tb < 0) throw new RangeError();
  return tb * 1024;
}
