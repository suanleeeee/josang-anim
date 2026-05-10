/* ============================================================
   당신의 조상은 아닙니다만 응원팀 정해드립니다 — main.js
   ============================================================ */

// ─── 구단 엠블럼 매핑 ────────────────────────────────────────
const EMBLEM_BASE = 'images/characters/26 구단 엠블럼/';
const EMBLEM = {
  'KT 위즈':       EMBLEM_BASE + 'KTwiz.svg',
  'LG 트윈스':     EMBLEM_BASE + 'LGtwins.svg',
  'SSG 랜더스':    EMBLEM_BASE + 'SSGlanders.svg',
  '삼성 라이온즈':  EMBLEM_BASE + 'SAMSUNGlions.svg',
  '기아 타이거즈':  EMBLEM_BASE + 'KIAtigers.svg',
  'NC 다이노스':    EMBLEM_BASE + 'NCdinos.svg',
  '두산 베어스':    EMBLEM_BASE + 'DOOSANbears.svg',
  '롯데 자이언츠':  EMBLEM_BASE + 'LOTTEgiants.svg',
  '한화 이글스':    EMBLEM_BASE + 'HANWHAeagles.svg',
  '키움 히어로즈':  EMBLEM_BASE + 'KIWOOMheroes.svg',
};

// ─── DOM 참조 ────────────────────────────────────────────────
const introSection   = document.getElementById('intro');
const resultSection  = document.getElementById('result');
const submitBtn      = document.getElementById('submitBtn');
const numberInput    = document.getElementById('favoriteNumber');
const loadingOverlay = document.getElementById('loadingOverlay');
const btnRetry       = document.getElementById('btnRetry');
const btnCopyLink    = document.getElementById('btnCopyLink');
const bgIntro        = document.getElementById('bg-intro');
const bgResult       = document.getElementById('bg-result');

const resultHeader      = document.getElementById('resultHeader');
const noCarryBanner     = document.getElementById('noCarryBanner');
const geongseongpaBanner = document.getElementById('geongseongpaBanner');
const resultTeamName    = document.getElementById('resultTeamName');
const cardsRow          = document.getElementById('cardsRow');
const fanTypesBadges    = document.getElementById('fanTypesBadges');
const fanTypeDesc       = document.getElementById('fanTypeDesc');
const fanReasonBox      = document.getElementById('fanReasonBox');
const fanReasonText     = document.getElementById('fanReasonText');
const fanTipBox         = document.getElementById('fanTipBox');
const btnAbout          = document.getElementById('btnAbout');
const aboutOverlay      = document.getElementById('aboutOverlay');
const aboutClose        = document.getElementById('aboutClose');

// ─── 유효성 검사 ─────────────────────────────────────────────
function validateInput() {
  const raw = numberInput.value.trim();
  const num = parseInt(raw, 10);
  if (raw === '' || isNaN(num) || num < 0 || num > 99) {
    numberInput.focus();
    numberInput.style.borderColor = '#f87171';
    numberInput.style.boxShadow   = '0 0 0 3px rgba(248,113,113,0.20)';
    setTimeout(() => {
      numberInput.style.borderColor = '';
      numberInput.style.boxShadow   = '';
    }, 1600);
    return null;
  }
  return num;
}

// ─── 로딩 토글 ───────────────────────────────────────────────
function setLoading(state) {
  loadingOverlay.classList.toggle('is-active', state);
}

// ─── 팀 카드 생성 ────────────────────────────────────────────
function buildTeamCard(t) {
  const card = document.createElement('div');
  card.className = 'team-card';

  // 구단 엠블럼
  const emblem = document.createElement('img');
  emblem.src = EMBLEM[t.team] || '';
  emblem.alt = t.team;
  emblem.className = 'card-emblem';

  // 팀명
  const name = document.createElement('p');
  name.className = 'card-team-name';
  name.textContent = t.team;

  // 급조팬지수
  const scoreWrap = document.createElement('div');
  scoreWrap.className = 'card-score-wrap';
  const scoreNum = document.createElement('span');
  scoreNum.className = 'card-score-num';
  scoreNum.textContent = t.fan_index;
  const scoreLabel = document.createElement('span');
  scoreLabel.className = 'card-score-label';
  scoreLabel.textContent = 'pt';
  scoreWrap.append(scoreNum, scoreLabel);

  card.append(emblem, name, scoreWrap);

  if (t.fan_index_desc) {
    const desc = document.createElement('p');
    desc.className = 'card-fan-index-desc';
    desc.textContent = t.fan_index_desc;
    card.appendChild(desc);
  }

  return card;
}

// ─── 결과 화면 렌더 ──────────────────────────────────────────
function renderResult(data) {
  const noCarry       = data.no_carry === true;
  const isGeongseongpa = !data.teams || data.teams.length === 0;

  resultHeader.classList.toggle('hidden', noCarry || isGeongseongpa);
  noCarryBanner.classList.toggle('hidden', !noCarry || isGeongseongpa);
  geongseongpaBanner.classList.toggle('hidden', !isGeongseongpa);

  const topTeam = data.teams && data.teams.length > 0 ? data.teams[0].team : '알 수 없음';
  resultTeamName.textContent = topTeam;

  cardsRow.innerHTML = '';
  const teams = data.teams || [];
  const topScore = teams.length > 0 ? teams[0].fan_index : 0;
  const podium = teams.length >= 3
    ? [teams[1], teams[0], teams[2]]
    : teams;
  podium.forEach((t, i) => {
    const card = buildTeamCard(t);
    const isCenter = teams.length >= 3 && i === 1;
    const isTiedTop = topScore >= 70 && t.fan_index === topScore;
    if (isCenter || isTiedTop) card.classList.add('rank-1');
    cardsRow.appendChild(card);
  });

  // 팬 타입 배지 + 확률
  fanTypesBadges.innerHTML = '';
  const types = data.fan_types || [];
  const probs = data.fan_type_probs || {};
  const displayTypes = types.length > 0 ? types : ['개성파'];

  displayTypes.forEach(t => {
    const badge = document.createElement('div');
    badge.className = 'fan-type-badge';

    const typeName = document.createElement('span');
    typeName.className = 'fan-type-name';
    typeName.textContent = t;

    badge.appendChild(typeName);

    if (probs[t] !== undefined) {
      const pct = document.createElement('span');
      pct.className = 'fan-type-pct';
      pct.textContent = `${probs[t]}%`;
      badge.appendChild(pct);
    }

    fanTypesBadges.appendChild(badge);
  });

  // 팬 타입 설명
  fanTypeDesc.textContent = isGeongseongpa
    ? '크보라는 우주에서 수많은 별을 마주하고 계시네요!'
    : (data.fan_type_desc || '이 번호 선수들의 특성을 분석했습니다.');

  // 1위 팀 추천 이유 / 팁
  fanReasonBox.classList.toggle('hidden', isGeongseongpa || noCarry);
  fanTipBox.classList.toggle('hidden', !isGeongseongpa);
  fanReasonText.textContent = data.teams && data.teams[0]
    ? data.teams[0].reason
    : '분석 데이터가 없습니다.';

  introSection.classList.add('hidden');
  resultSection.classList.remove('hidden');
  bgIntro.classList.add('hidden');
  bgResult.classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ─── API 호출 ────────────────────────────────────────────────
async function fetchRecommendation(number) {
  const res = await fetch(`/api/recommend?number=${number}`);
  if (!res.ok) throw new Error(`서버 오류: ${res.status}`);
  return res.json();
}

// ─── 제출 핸들러 ─────────────────────────────────────────────
async function handleSubmit() {
  const num = validateInput();
  if (num === null) return;

  setLoading(true);
  try {
    const data = await fetchRecommendation(num);
    renderResult(data);
  } catch (err) {
    console.error(err);
    alert('결과를 불러오는 데 실패했습니다. 잠시 후 다시 시도해 주세요.');
  } finally {
    setLoading(false);
  }
}

submitBtn.addEventListener('click', handleSubmit);
numberInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') handleSubmit();
});

// ─── 다시하기 ────────────────────────────────────────────────
btnRetry.addEventListener('click', () => {
  resultSection.classList.add('hidden');
  introSection.classList.remove('hidden');
  bgResult.classList.add('hidden');
  bgIntro.classList.remove('hidden');
  numberInput.value = '';
  numberInput.focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ─── 링크 복사 ───────────────────────────────────────────────
btnCopyLink.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(location.href);
    const orig = btnCopyLink.textContent;
    btnCopyLink.textContent = '복사 완료!';
    setTimeout(() => { btnCopyLink.textContent = orig; }, 1800);
  } catch {
    alert('링크를 복사해 주세요: ' + location.href);
  }
});

// ─── About 모달 ──────────────────────────────────────────────
const aboutPage1      = document.getElementById('aboutPage1');
const aboutPage2      = document.getElementById('aboutPage2');
const btnToReviews    = document.getElementById('btnToReviews');
const btnBackToAbout  = document.getElementById('btnBackToAbout');

function openAbout() {
  aboutPage1.classList.remove('hidden');
  aboutPage2.classList.add('hidden');
  aboutOverlay.classList.remove('hidden');
}
function closeAbout() {
  aboutOverlay.classList.add('hidden');
}

btnAbout.addEventListener('click', openAbout);
aboutClose.addEventListener('click', closeAbout);
aboutOverlay.addEventListener('click', e => { if (e.target === aboutOverlay) closeAbout(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAbout(); });

btnToReviews.addEventListener('click', () => {
  aboutPage1.classList.add('hidden');
  aboutPage2.classList.remove('hidden');
});
btnBackToAbout.addEventListener('click', () => {
  aboutPage2.classList.add('hidden');
  aboutPage1.classList.remove('hidden');
});

// ─── 이미지 저장 ─────────────────────────────────────────────
const btnSaveImage = document.getElementById('btnSaveImage');
btnSaveImage.addEventListener('click', async () => {
  btnSaveImage.disabled = true;
  const w = window.innerWidth;

  // 캡처 전용 wrapper 생성
  const wrapper = document.createElement('div');
  wrapper.style.cssText = `position:absolute;left:${w}px;top:0;width:${w}px;overflow:hidden;background-color:#0D1A3A;`;

  // SVG 배경 클론 (fixed → absolute로 변환)
  const bgSvg = document.getElementById('bg-result').cloneNode(true);
  bgSvg.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;z-index:0;';
  bgSvg.classList.remove('hidden');
  wrapper.appendChild(bgSvg);

  // 결과 콘텐츠 클론 (share-area 제거)
  const resultClone = document.getElementById('result').cloneNode(true);
  resultClone.style.cssText = 'position:relative;z-index:1;background:transparent;min-height:0;';
  resultClone.classList.remove('hidden');
  resultClone.querySelector('.share-area')?.remove();

  // 경고문 추가
  const notice = document.createElement('p');
  notice.textContent = '실제 선수 추천·투자 등과 무관한 재미용 서비스입니다.';
  notice.style.cssText = 'text-align:center;font-size:0.60rem;color:rgba(180,160,120,0.5);padding:10px 24px 28px;letter-spacing:0.04em;';
  resultClone.appendChild(notice);

  wrapper.appendChild(resultClone);
  document.body.appendChild(wrapper);

  try {
    const canvas = await html2canvas(wrapper, {
      useCORS: true,
      allowTaint: true,
      scale: 2,
      backgroundColor: '#0D1A3A',
    });
    document.body.removeChild(wrapper);
    const link = document.createElement('a');
    link.download = `조상은아니고요_${resultTeamName.textContent || '결과'}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  } catch {
    document.body.removeChild(wrapper);
    alert('이미지 저장에 실패했어요. 다시 시도해 주세요.');
  } finally {
    btnSaveImage.disabled = false;
  }
});
