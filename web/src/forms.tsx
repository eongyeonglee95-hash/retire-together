import { useState, type FormEvent } from 'react'
import { ArrowRight, Check, Info, Pencil, Plus, Trash2 } from 'lucide-react'
import { api } from './local-data'
import { classInfo, money, type Asset, type Family, type Owner } from './model'

const roles = { wife: '아내', husband: '남편', partner: '배우자' }
export const personRole = (role: keyof typeof roles) => roles[role]
function ErrorBox({ error }: { error: string }) { return error ? <div className="form-error" role="alert"><Info size={16}/>{error}</div> : null }

export function ProfileForm({ family, onSaved }: { family: Family | null; onSaved: () => void }) {
  const [withPartner, setWithPartner] = useState(!!family?.partner)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError('')
    const data = new FormData(e.currentTarget)
    const person = (key: 'me' | 'partner') => ({ name: data.get(`${key}-name`), age: Number(data.get(`${key}-age`)), role: data.get(`${key}-role`), gender: data.get(`${key}-gender`) })
    try {
      await api('/family', 'PUT', { me: person('me'), partner: withPartner ? person('partner') : null, retirement_age: Number(data.get('retirement_age')), target_amount: Number(data.get('target_amount')) * 10_000, version: family?.version ?? 0 })
      onSaved()
    } catch (e) { setError(e instanceof Error ? e.message : '저장하지 못했습니다.') } finally { setBusy(false) }
  }
  return <form onSubmit={submit}>
    <p className="form-intro">누구의 자산인지부터 정확하게.<br/>입력한 정보는 이 컴퓨터에 저장됩니다.</p>
    {(['me', ...(withPartner ? ['partner'] : [])] as ('me' | 'partner')[]).map(key => <fieldset className="profile-fields" key={key}><legend>{key === 'me' ? '내 정보' : '배우자 정보'}</legend><div className="form-grid"><label className="form-label">이름 또는 별명<input name={`${key}-name`} defaultValue={family?.[key]?.name ?? ''} placeholder={key === 'me' ? '나를 부를 이름' : '배우자를 부를 이름'} maxLength={40} required autoComplete="off"/></label><label className="form-label">현재 만 나이<input name={`${key}-age`} type="number" min="18" max="110" step="1" defaultValue={family?.[key]?.age ?? ''} placeholder="예: 40" required/></label><label className="form-label">{key === 'me' ? '나는' : '배우자는'}<select name={`${key}-role`} defaultValue={family?.[key]?.role ?? ''} required><option value="" disabled>역할을 선택하세요</option value="wife">아내</option><option value="husband">남편</option><option value="partner">배우자 (기타)</option></select></label><label className="form-label">성별 · 선택<select name={`${key}-gender`} defaultValue={family?.[key]?.gender ?? 'unspecified'}><option value="unspecified">선택하지 않음</option><option value="female">여성</option><option value="male">남성</option></select></label></div></fieldset>)}
    <label className="checkbox-label"><input type="checkbox" checked={withPartner} onChange={e => setWithPartner(e.target.checked)}/>배우자 정보도 함께 입력하기</label>
    <fieldset className="profile-fields"><legend>우리의 은퇴 목표</legend><div className="form-grid"><label className="form-label">목표 은퇴 나이 (나 기준)<input name="retirement_age" type="number" min="18" max="100" step="1" defaultValue={family?.retirement_age ?? 62} required/></label><label className="form-label">목표 순자산 (만원)<input name="target_amount" type="number" min="1" max="100000000000" step="1" defaultValue={family ? family.target_amount / 10_000 : 300000} required/></label></div><p className="form-help">현재 만 나이는 입력한 시점 기준입니다. 생일이 지나면 수정해 주세요. 성별과 가족 역할은 서로 독립된 선택입니다.</p></fieldset>
    <ErrorBox error={error}/><button type="submit" className="primary-button full-width" disabled={busy}>{busy ? '저장 중…' : '내 정보 저장'}<Check size={16}/></button>
  </form>
}

export function AssetForm({ family, asset, owner, onSaved, onProfile }: { family: Family | null; asset: Asset | null; owner: Owner; onSaved: () => void; onProfile: () => void }) {
  const [pocket, setPocket] = useState(asset?.pocket ?? 'retirement')
  const [amount, setAmount] = useState(String(asset?.amount ?? ''))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [requestId] = useState(() => crypto.randomUUID())
  const today = new Date().toLocaleDateString('en-CA')
  if (!family) return <div className="empty-state"><Info size={28}/><h3>먼저 내 정보를 알려주세요</h3><p>누구의 자산인지 구분할 수 있도록<br/>내 정보와 필요한 경우 배우자 정보를 등록해 주세요.</p><button className="primary-button" onClick={onProfile}>내 정보 입력하기 <ArrowRight size={16}/></button></div>
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError('')
    const data = new FormData(e.currentTarget)
    const body = { name: data.get('name'), account: data.get('account'), owner: data.get('owner'), pocket, assetClass: pocket === 'debt' || pocket === 'property' ? pocket : data.get('assetClass'), amount: Number(data.get('amount')), as_of: data.get('as_of'), ...(asset ? { version: asset.version } : { request_id: requestId }) }
    try { await api(asset ? `/assets/${asset.id}` : '/assets', asset ? 'PUT' : 'POST', body); onSaved() }
    catch (e) { setError(e instanceof Error ? e.message : '저장하지 못했습니다.') } finally { setBusy(false) }
  }
  return <form onSubmit={submit}><p className="form-intro">우선 계좌나 자산의 현재 금액부터 입력해요.<br/>계좌 전체 금액과 그 안의 종목을 중복 등록하지 마세요.</p><div className="form-grid"><label className="form-label">누구의 자산인가요?<select name="owner" defaultValue={asset?.owner ?? (owner === 'partner' && family.partner ? 'partner' : 'me')} required><option value="me">나 · {family.me.name} ({roles[family.me.role]})</option>{family.partner && <option value="partner">배우자 · {family.partner.name} ({roles[family.partner.role]})</option>}</select></label><label className="form-label">자산 종류<select value={pocket} onChange={e => setPocket(e.target.value as Asset['pocket'])}><option value="retirement">노후 주머니 (연금)</option><option value="cash">현금 주머니 (예금·투자)</option><option value="property">부동산</option><option value="debt">대출·부채</option></select></label></div><label className="form-label">자산 이름<input name="name" defaultValue={asset?.name ?? ''} placeholder={pocket === 'debt' ? '예: 주택담보대출' : '예: 내 연금저축, 우리 집'} maxLength={100} required/></label><label className="form-label">계좌 또는 보관처 이름<input name="account" defaultValue={asset?.account ?? ''} placeholder="예: 미래에셋 연금저축 (계좌번호 입력 불필요)" maxLength={100} required/></label>{pocket !== 'debt' && pocket !== 'property' && <label className="form-label">자산군<select name="assetClass" defaultValue={asset?.assetClass === 'debt' || asset?.assetClass === 'property' ? 'mixed' : asset?.assetClass ?? 'mixed'}>{Object.entries(classInfo).filter(([k]) => k !== 'property' && k !== 'debt').map(([key, info]) => <option key={key} value={key}>{info.label}</option>)}</select><small>계좌에 여러 자산군이 섞여 있으면 ‘혼합·미분류’를 선택하세요.</small></label>}<div className="form-grid"><label className="form-label">{pocket === 'debt' ? '남은 대출 잔액' : pocket === 'property' ? '선택한 소유자의 지분 금액' : '현재 평가 금액'} (원)<input name="amount" type="number" min="0" max="1000000000000000" step="1" value={amount} onChange={e => setAmount(e.target.value)} placeholder="숫자로 입력" required/><small>{amount && Number.isFinite(Number(amount)) ? money(Number(amount)) : '원 단위로 입력하세요'}</small></label><label className="form-label">금액 기준일<input name="as_of" type="date" defaultValue={asset?.as_of ?? today} max={today} required/></label></div>{pocket === 'property' && <p className="form-help">공동 소유라면 집 전체 금액이 아닌, 선택한 소유자의 지분 금액을 입력해요.</p>}<ErrorBox error={error}/><button type="submit" className="primary-button full-width" disabled={busy}>{asset ? <Pencil size={16}/> : <Plus size={16}/>} {busy ? '저장 중…' : asset ? '수정 내용 저장' : '자산 등록하기'}</button></form>
}

export function DeleteAsset({ asset, onDeleted, onCancel }: { asset: Asset; onDeleted: () => void; onCancel: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  return <><p className="modal-lead">이 자산을 목록에서 삭제할까요?</p><p>{asset.name} · {money(asset.amount)}<br/>현재 자산 합계에서도 제외됩니다. 이전 변경 이력은 로컬 DB에 보관됩니다.</p><ErrorBox error={error}/><div className="button-row delete-actions"><button className="secondary-button" disabled={busy} onClick={onCancel}>돌아가기</button><button className="danger-button" disabled={busy} onClick={async () => { setBusy(true); try { await api(`/assets/${asset.id}?version=${asset.version}`, 'DELETE'); onDeleted() } catch (e) { setError(e instanceof Error ? e.message : '삭제하지 못했습니다.'); setBusy(false) } }}><Trash2 size={15}/>{busy ? '삭제 중…' : '삭제하기'}</button></div></>
}
