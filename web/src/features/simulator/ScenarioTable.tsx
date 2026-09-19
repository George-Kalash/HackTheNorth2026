import {money,type Opportunity} from '../../services/api';
export function ScenarioTable({result}:{result:Opportunity}){return <table><thead><tr><th>Resolution scenario</th><th>Combined payout</th></tr></thead><tbody>{result.scenarios.map(s=><tr key={s.name}><td>{s.name}</td><td>{money(s.total)}</td></tr>)}</tbody></table>}
