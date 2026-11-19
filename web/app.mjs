import {$,node,link,options,load} from './ui.mjs';
import {matches,historyLines} from './model.mjs';
load(data => {
  options('region',['All areas',...new Set(data.offices.map(o=>o.region))]);
  function render() {
    if (!$('date').validity.valid) {
      $('cards').replaceChildren();
      $('summary').textContent = 'Choose a valid date from 1700 to 1968, or clear the date to browse the histories.';
      return;
    }
    const date = $('date').value;
    const selected = matches(data.offices,$('search').value,date,$('region').value);
    $('summary').textContent = selected.length ? selected.length+' matching office '+(selected.length===1?'history':'histories')+(date?' · '+date:' · all dates') : 'No matching office in these sources. Try another spelling, change the date or browse all histories.';
    $('cards').replaceChildren(...selected.map(({office,state}) => {
      const card = node('article',undefined,'card');
      card.append(node('p',office.region,'minitag'),node('h3',state?.name || office.names.map(n=>n.name).join(' → ')));
      if (state?.uncertain) card.append(node('p','Possible match. The source gives an approximate opening date.','callout'));
      const list = node('ul',undefined,'history');
      for (const [when,what] of historyLines(office)) {
        const item=node('li'); item.append(node('strong',when+' '),document.createTextNode(what)); list.append(item);
      }
      card.append(list);
      if (!office.closed) card.append(node('p','No closure is documented in this excerpt.','minor'));
      card.append(link(office.region === 'Dartmouth, NS' ? 'Dartmouth heritage report · PDF p. 23 ↗' : 'Township report · printed p. 64 ↗', office.source));
      return card;
    }));
  }
  function preset(text,date) {
    $('search').value=text; $('date').value=date; $('region').value='All areas'; render();
  }
  $('earlier').onclick=()=>preset('Langley Prairie','1910-05-16');
  $('later').onclick=()=>preset('Langley Prairie','1912-05-16');
  $('dart').onclick=()=>preset('Dartmouth','1894-01-01');
  $('all').onclick=()=>preset('','');
  $('search').oninput=render; $('date').oninput=render; $('region').onchange=render;
  render();
});
