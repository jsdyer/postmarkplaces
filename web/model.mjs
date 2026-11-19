function stateAt(office, date) {
  if (office.closed && date >= office.closed) return null;
  const name = [...office.names].reverse().find(n => !n.from || n.from <= date);
  if (!name) return null;
  const uncertain = (!name.from && date < office.before) || (name.from?.length === 4 && date.startsWith(name.from));
  return {name: name.name, uncertain};
}
export function matches(offices, query, date, area) {
  const text = query.trim().toLowerCase();
  return offices.flatMap(office => {
    if (area !== 'All areas' && area !== office.region) return [];
    const state = date ? stateAt(office, date) : null;
    if (date && (!state || !state.name.toLowerCase().includes(text))) return [];
    if (!date && !office.names.some(n => n.name.toLowerCase().includes(text))) return [];
    return [{office, state}];
  });
}
export function historyLines(office) {
  const events = office.names.map((n,i) => [n.from || 'Before '+office.before.slice(0,4), (i ? 'Renamed ' : 'Established as ')+n.name+'.']);
  if (office.closed) events.push([office.closed,'Office closed.']);
  for (const [year,note] of office.events || []) {
    if (events.find(e => e[0] === year)) events.find(e => e[0] === year)[1] = note;
    else events.push([year,note]);
  }
  return events;
}
