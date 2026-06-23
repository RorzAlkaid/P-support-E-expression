<script setup>
import axios from 'axios'
import * as echarts from 'echarts'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import heroImage from './assets/landing-hero.png'
import logoMark from './assets/xinqing-logo-mark.svg'

const authMode = ref('login')
const showAuth = ref(false)
const inkX = ref('50vw')
const inkY = ref('28vh')
const inkActive = ref(0.38)
const scrollShift = ref('0px')
const loading = ref(true)
const dashboard = ref(null)
const moodTrend = ref([])
const pressureData = ref([])
const counselors = ref([])
const articles = ref([])
const trendChartRef = ref(null)
const pressureChartRef = ref(null)
let trendChart = null
let pressureChart = null
let chartResizeObserver = null
let chartVisibilityObserver = null
let chartRenderTimer = null
let chartRenderAttempts = 0
const maxChartRenderAttempts = 12
const currentUser = ref(null)
const initialHashParts = window.location.hash?.replace('#/', '').split('/') || ['home']
const currentPage = ref(initialHashParts[0] || 'home')
const authSubmitting = ref(false)
const authMessage = ref('')
const moduleData = ref(null)
const moduleMessage = ref('')
const currentArticleId = ref(initialHashParts[0] === 'article' ? initialHashParts[1] : null)
const activeModule = ref('mood')
const resourcePage = ref(1)
const resourcePageSize = 24
const moodForm = ref({
  mood: '平静',
  intensity: 6,
  sleep_quality: 6,
  pressure_sources: '学业压力',
  note: '',
})
const treeholeForm = ref({
  category: 'study',
  mood_tag: '焦虑',
  content: '',
})
const assessmentForm = ref({
  scale: null,
  answers: [],
})
const appointmentForm = ref({
  counselor: null,
  scheduled_at: '',
  topic: '',
  confidential_note: '',
})
const replyForms = ref({})
const authForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  role: '学生',
  name: '',
  email: '',
  studentNo: '',
  college: '',
  grade: '',
  pressureSources: '',
  preferredTopics: '',
  privacyConsent: false,
})

const pageTitles = {
  home: '首页',
  register: '账号注册',
  details: '平台详情',
  article: '文章详情',
  mood: '情绪打卡',
  treehole: '匿名树洞',
  assessment: '心理测评',
  appointment: '咨询预约',
  resources: '心理资源',
  alerts: '预警管理',
}

const moduleIntros = [
  {
    page: 'mood',
    title: '情绪打卡',
    stat: '趋势记录',
    text: '记录每日情绪、睡眠质量、压力来源和私密日记，形成可追踪的情绪变化数据。',
    points: ['情绪强度', '睡眠质量', '压力来源'],
  },
  {
    page: 'treehole',
    title: '匿名树洞',
    stat: '匿名表达',
    text: '为学生提供低压力表达入口，支持匿名发布、同伴回应和高风险内容提醒。',
    points: ['匿名发布', '温和回应', '风险标记'],
  },
  {
    page: 'assessment',
    title: '心理测评',
    stat: '自助筛查',
    text: '通过量表题目生成得分、风险等级和建议，帮助学生初步理解当前状态。',
    points: ['量表答题', '风险等级', '建议反馈'],
  },
  {
    page: 'appointment',
    title: '咨询预约',
    stat: '专业对接',
    text: '按咨询师、时间和主题提交预约，帮助学生从自助支持进入专业支持流程。',
    points: ['咨询师选择', '预约记录', '保密备注'],
  },
  {
    page: 'resources',
    title: '心理资源',
    stat: '动态内容',
    text: '集中展示心理科普文章和自助干预内容，为学生提供可持续的日常支持。',
    points: ['科普文章', '自助练习', '主题标签'],
  },
  {
    page: 'alerts',
    title: '预警管理',
    stat: '持续关怀',
    text: '汇总高风险测评、情绪低谷和危机表达，辅助教师与管理员及时跟进。',
    points: ['风险预警', '处理状态', '后台管理'],
  },
]

const moduleDetails = [
  {
    page: 'mood',
    title: '情绪打卡',
    summary: '用于持续记录学生每天的情绪、睡眠质量、压力来源和私密日记，帮助学生和心理教师发现状态变化。',
    student: ['提交每日情绪记录', '查看个人情绪趋势', '记录压力来源和睡眠情况', '在低谷时获得后续支持入口'],
    teacher: ['查看已录入的情绪数据', '关注持续低情绪或睡眠异常', '结合量表和预约记录判断是否需要跟进'],
    data: ['情绪标签', '情绪强度', '睡眠质量', '压力来源', '日记内容'],
  },
  {
    page: 'treehole',
    title: '匿名树洞',
    summary: '为学生提供低压力表达空间，支持匿名倾诉和温和回应，同时对高风险表达进行标记。',
    student: ['匿名发布困扰', '查看同伴回应', '回应他人的表达', '在安全氛围中获得支持'],
    teacher: ['浏览树洞内容', '识别高风险表达', '通过后台进行必要跟进', '维护社区表达秩序'],
    data: ['分类', '情绪标签', '匿名内容', '回应内容', '风险标记'],
  },
  {
    page: 'assessment',
    title: '心理测评',
    summary: '通过简短量表完成自助筛查，系统自动生成得分、风险等级和建议。',
    student: ['选择量表答题', '查看测评结果', '获得分层建议', '根据结果进入预约流程'],
    teacher: ['查看测评记录', '关注中高风险学生', '结合情绪数据辅助判断', '制定后续干预方案'],
    data: ['量表题目', '答题记录', '测评分数', '风险等级', '反馈建议'],
  },
  {
    page: 'appointment',
    title: '咨询预约',
    summary: '帮助学生根据咨询师擅长领域和可预约时间发起咨询请求，形成专业对接流程。',
    student: ['选择咨询师', '提交预约时间', '填写咨询主题', '查看预约状态'],
    teacher: ['查看预约队列', '确认或跟进预约', '结合备注了解来访需求', '管理排班与服务记录'],
    data: ['咨询师', '预约时间', '咨询主题', '预约状态', '保密备注'],
  },
  {
    page: 'resources',
    title: '心理资源',
    summary: '集中展示心理科普文章、自助练习和求助指南，为学生提供日常心理健康支持。',
    student: ['浏览心理科普', '按主题理解压力与情绪', '获取自助练习方法', '了解求助时机'],
    teacher: ['维护资源内容', '按学生需求推荐文章', '辅助开展心理健康教育', '持续更新知识库'],
    data: ['文章标题', '来源', '分类', '摘要', '标签'],
  },
  {
    page: 'alerts',
    title: '预警管理',
    summary: '汇总量表高分、低情绪记录和危机表达，为教师和管理员提供持续关怀线索。',
    student: ['触发预警后获得关注', '通过预约和记录进入支持流程', '保留必要的隐私边界'],
    teacher: ['查看未处理预警', '识别需要跟进的学生', '记录处理结果', '推动持续关怀闭环'],
    data: ['学生信息', '预警等级', '触发原因', '处理状态', '处理记录'],
  },
]

const currentRole = computed(() => currentUser.value?.role || 'guest')
const canWrite = computed(() => ['student', 'admin'].includes(currentRole.value))
const canManage = computed(() => currentRole.value === 'admin')
const canViewAlerts = computed(() => ['teacher', 'admin'].includes(currentRole.value))
const canOperateAppointments = computed(() => ['teacher', 'admin'].includes(currentRole.value))
const canPublishTreehole = computed(() => ['student', 'admin'].includes(currentRole.value))
const canReplyTreehole = computed(() => ['student', 'teacher', 'admin'].includes(currentRole.value))
const currentArticle = computed(() => articles.value.find((item) => String(item.id) === String(currentArticleId.value)))
const homeCounselors = computed(() => counselors.value.slice(0, 6))
const homeArticles = computed(() => articles.value.slice(0, 6))
const resourceTotalPages = computed(() => Math.max(1, Math.ceil(articles.value.length / resourcePageSize)))
const pagedArticles = computed(() => {
  const page = Math.min(resourcePage.value, resourceTotalPages.value)
  const start = (page - 1) * resourcePageSize
  return articles.value.slice(start, start + resourcePageSize)
})
const visibleAppointments = computed(() => {
  const appointments = moduleData.value?.appointments || []
  if (['teacher', 'admin'].includes(currentRole.value)) return appointments
  return appointments.filter((item) => !['pending', 'cancelled'].includes(item.status))
})
const readonlyReason = computed(() => {
  if (currentRole.value === 'guest') return '未登录用户只能浏览已经录入的数据，不能新增或修改。'
  if (currentRole.value === 'teacher') return '教师账号仅可查询学生数据和平台内容，不能新增或修改。'
  return ''
})

function handlePointerMove(event) {
  inkX.value = `${event.clientX}px`
  inkY.value = `${event.clientY}px`
  inkActive.value = 0.72
}

function handlePointerLeave() {
  inkActive.value = 0.28
}

function handleScroll() {
  const shift = Math.min(window.scrollY * 0.026, 34)
  scrollShift.value = `${shift.toFixed(2)}px`
}

function navigate(page) {
  if (page === 'alerts' && !canViewAlerts.value) {
    currentPage.value = 'home'
    window.location.hash = '/home'
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return
  }
  currentPage.value = page
  window.location.hash = `/${page}`
  window.scrollTo({ top: 0, behavior: 'smooth' })
  if (page !== 'home') {
    refreshModules()
  }
}

function openArticle(article) {
  currentArticleId.value = article.id
  currentPage.value = 'article'
  window.location.hash = `/article/${article.id}`
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function scrollToModules() {
  document.querySelector('#modules')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function startExperience() {
  if (currentUser.value) {
    navigate('details')
    return
  }
  openAuth('login')
}

async function loadBackendData() {
  try {
    const [dashboardRes, trendRes, pressureRes, counselorsRes, articlesRes, moduleRes] = await Promise.all([
      axios.get('/api/dashboard/'),
      axios.get('/api/mood-trend/'),
      axios.get('/api/pressure-distribution/'),
      axios.get('/api/recommendations/counselors/?student=1'),
      axios.get('/api/articles/'),
      axios.get('/api/modules/'),
    ])

    dashboard.value = dashboardRes.data
    moodTrend.value = trendRes.data
    pressureData.value = pressureRes.data
    counselors.value = counselorsRes.data
    articles.value = articlesRes.data.results ?? articlesRes.data
    moduleData.value = moduleRes.data
    const firstScale = moduleRes.data.scales?.[0]
    const firstCounselor = moduleRes.data.counselors?.[0]
    if (firstScale && !assessmentForm.value.scale) {
      assessmentForm.value.scale = firstScale.id
      assessmentForm.value.answers = firstScale.questions.map(() => 1)
    }
    if (firstCounselor && !appointmentForm.value.counselor) {
      appointmentForm.value.counselor = firstCounselor.id
    }
    loading.value = false
    await nextTick()
    setupChartObservers()
    scheduleRenderCharts()
  } catch (error) {
    loading.value = false
    console.error('Django API 数据加载失败', error)
  }
}

async function refreshModules() {
  const [moduleRes, dashboardRes, trendRes, pressureRes] = await Promise.all([
    axios.get('/api/modules/'),
    axios.get('/api/dashboard/'),
    axios.get('/api/mood-trend/'),
    axios.get('/api/pressure-distribution/'),
  ])
  moduleData.value = moduleRes.data
  dashboard.value = dashboardRes.data
  moodTrend.value = trendRes.data
  pressureData.value = pressureRes.data
  await nextTick()
  setupChartObservers()
  scheduleRenderCharts()
}

async function loadCurrentUser() {
  const response = await axios.get('/api/auth/me/')
  currentUser.value = response.data.authenticated ? response.data.user : null
}

function chartReady(el) {
  return el && el.clientWidth > 0 && el.clientHeight > 0
}

function scheduleRenderCharts({ retry = false } = {}) {
  if (currentPage.value !== 'home') return
  if (!retry) chartRenderAttempts = 0
  window.clearTimeout(chartRenderTimer)
  chartRenderTimer = window.setTimeout(async () => {
    await nextTick()
    requestAnimationFrame(() => {
      const rendered = renderCharts()
      resizeCharts()
      if (!rendered && currentPage.value === 'home' && chartRenderAttempts < maxChartRenderAttempts) {
        chartRenderAttempts += 1
        scheduleRenderCharts({ retry: true })
      }
    })
  }, retry ? 80 : 0)
}

function resizeCharts() {
  trendChart?.resize()
  pressureChart?.resize()
}

function setupChartObservers() {
  const targets = [trendChartRef.value, pressureChartRef.value].filter(Boolean)
  if (!targets.length) return

  if (!chartResizeObserver) {
    chartResizeObserver = new ResizeObserver(() => {
      scheduleRenderCharts()
    })
  }

  if (!chartVisibilityObserver) {
    chartVisibilityObserver = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          scheduleRenderCharts()
        }
      },
      { threshold: 0.15 },
    )
  }

  targets.forEach((target) => {
    chartResizeObserver.observe(target)
    chartVisibilityObserver.observe(target)
  })
}

function renderCharts() {
  let renderedTrend = false
  let renderedPressure = false

  if (chartReady(trendChartRef.value)) {
    trendChart = trendChart || echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { top: 0, data: ['情绪强度', '睡眠质量'] },
      grid: { top: 44, right: 20, bottom: 28, left: 34 },
      xAxis: { type: 'category', data: moodTrend.value.map((item) => item.date) },
      yAxis: { type: 'value', min: 0, max: 10 },
      series: [
        {
          name: '情绪强度',
          type: 'line',
          smooth: true,
          data: moodTrend.value.map((item) => item.intensity),
          lineStyle: { color: '#d85d73', width: 3 },
          itemStyle: { color: '#d85d73' },
          areaStyle: { color: 'rgba(216, 93, 115, 0.12)' },
        },
        {
          name: '睡眠质量',
          type: 'line',
          smooth: true,
          data: moodTrend.value.map((item) => item.sleep_quality),
          lineStyle: { color: '#4c8f8a', width: 3 },
          itemStyle: { color: '#4c8f8a' },
        },
      ],
    })
    renderedTrend = true
  }

  if (chartReady(pressureChartRef.value)) {
    pressureChart = pressureChart || echarts.init(pressureChartRef.value)
    pressureChart.setOption({
      tooltip: {},
      radar: {
        indicator: pressureData.value.map((item) => ({ name: item.name, max: 8 })),
        radius: '64%',
      },
      series: [
        {
          type: 'radar',
          data: [{ value: pressureData.value.map((item) => item.value), name: '压力来源' }],
          areaStyle: { color: 'rgba(240, 173, 99, 0.22)' },
          lineStyle: { color: '#f0ad63', width: 3 },
          itemStyle: { color: '#f0ad63' },
        },
      ],
    })
    renderedPressure = true
  }

  return renderedTrend && renderedPressure
}

watch([currentPage, moodTrend, pressureData, currentUser], async () => {
  if (currentPage.value !== 'home' || loading.value) return
  await nextTick()
  setupChartObservers()
  scheduleRenderCharts()
}, { flush: 'post' })

onMounted(() => {
  handleScroll()
  loadBackendData()
  loadCurrentUser()
  window.addEventListener('pointermove', handlePointerMove)
  window.addEventListener('scroll', handleScroll, { passive: true })
  window.addEventListener('resize', scheduleRenderCharts)
  window.addEventListener('hashchange', () => {
    const parts = window.location.hash?.replace('#/', '').split('/') || ['home']
    const nextPage = parts[0] || 'home'
    if (nextPage === 'alerts' && !canViewAlerts.value) {
      navigate('home')
      return
    }
    currentPage.value = nextPage
    currentArticleId.value = parts[0] === 'article' ? parts[1] : currentArticleId.value
  })
})

onUnmounted(() => {
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', scheduleRenderCharts)
  window.clearTimeout(chartRenderTimer)
  chartResizeObserver?.disconnect()
  chartVisibilityObserver?.disconnect()
  trendChart?.dispose()
  pressureChart?.dispose()
})

const features = [
  {
    title: '情绪打卡',
    subtitle: '记录每天的心情变化',
    desc: '用表情、强度和影响因素记录每天的状态，形成连续的情绪轨迹。',
    stat: '7 日趋势',
    accent: 'rose',
    detail: '支持心情标签、压力来源、睡眠状态和简短日记，自动生成近一周趋势，让学生更早看见自己的变化。',
  },
  {
    title: '匿名树洞',
    subtitle: '把难说出口的烦恼放下来',
    desc: '把难以开口的困扰安全表达出来，获得同伴温和回应与支持。',
    stat: '匿名表达',
    accent: 'pink',
    detail: '发布内容默认匿名，结合关键词提醒与温和引导，帮助学生在被理解的氛围里表达压力、关系和成长困惑。',
  },
  {
    title: '心理测评',
    subtitle: '自助了解压力与风险信号',
    desc: '提供压力、睡眠、情绪等自评问卷，结果只作风险提示与资源推荐。',
    stat: '自助筛查',
    accent: 'amber',
    detail: '测评结果以非诊断方式呈现，提供分层建议、资源链接和后续跟进入口，避免给学生制造额外负担。',
  },
  {
    title: '咨询预约',
    subtitle: '让正式求助更容易开始',
    desc: '查看心理老师时间、擅长方向与预约状态，减少求助过程中的心理负担。',
    stat: '线上预约',
    accent: 'plum',
    detail: '学生可按时间、方向和紧急程度预约，教师端同步处理排班、备注、回访与必要的风险提醒。',
  },
]

const scenes = [
  {
    label: '学生',
    title: '表达、记录、求助',
    text: '从一句日记到一次正式预约，平台把不同强度的心理支持放在同一个入口里。',
  },
  {
    label: '教师',
    title: '看见趋势，及时响应',
    text: '教师端聚合预约、测评和预警信息，帮助心理中心更早发现需要支持的学生。',
  },
  {
    label: '学校',
    title: '构建温和的支持网络',
    text: '用数据看整体压力变化，用内容和服务形成校园心理健康支持闭环。',
  },
]

const steps = [
  '学生完成情绪打卡或匿名表达',
  '系统形成趋势、标签和风险提示',
  '推荐自助资源或发起咨询预约',
  '心理老师处理预警并持续回访',
]

function openAuth(mode) {
  if (mode === 'register') {
    showAuth.value = false
    authMode.value = 'register'
    authMessage.value = ''
    navigate('register')
    return
  }
  authMode.value = mode
  showAuth.value = true
  authMessage.value = ''
  authForm.value.password = ''
  authForm.value.confirmPassword = ''
}

async function submitAuth() {
  authSubmitting.value = true
  authMessage.value = ''

  try {
    const payload = {
      username: authForm.value.username,
      password: authForm.value.password,
    }
    const response = await axios.post('/api/auth/login/', payload)
    currentUser.value = response.data.user
    authMessage.value = response.data.detail || '操作成功'
    showAuth.value = false
    await refreshModules()
  } catch (error) {
    authMessage.value = error.response?.data?.detail || '操作失败，请检查输入后重试。'
  } finally {
    authSubmitting.value = false
  }
}

async function submitRegister() {
  authSubmitting.value = true
  authMessage.value = ''

  try {
    const payload = {
      username: authForm.value.username,
      password: authForm.value.password,
      confirm_password: authForm.value.confirmPassword,
      role: authForm.value.role,
      name: authForm.value.name,
      email: authForm.value.email,
      student_no: authForm.value.studentNo,
      college: authForm.value.college,
      grade: authForm.value.grade,
      pressure_sources: pressureSourceList(authForm.value.pressureSources),
      preferred_topics: pressureSourceList(authForm.value.preferredTopics),
      privacy_consent: authForm.value.privacyConsent,
    }
    const response = await axios.post('/api/auth/register/', payload)
    currentUser.value = response.data.user
    authMessage.value = response.data.detail || '注册成功'
    await refreshModules()
    navigate('details')
  } catch (error) {
    authMessage.value = error.response?.data?.detail || '注册失败，请检查输入后重试。'
  } finally {
    authSubmitting.value = false
  }
}

async function logoutAccount() {
  await axios.post('/api/auth/logout/')
  currentUser.value = null
}

function pressureSourceList(value) {
  return String(value || '')
    .split(/[，,、\s]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

async function submitMood() {
  if (!canWrite.value) {
    moduleMessage.value = readonlyReason.value
    return
  }
  const payload = {
    ...moodForm.value,
    intensity: Number(moodForm.value.intensity),
    sleep_quality: Number(moodForm.value.sleep_quality),
    pressure_sources: pressureSourceList(moodForm.value.pressure_sources),
    is_private: true,
  }
  await axios.post('/api/modules/moods/', payload)
  moodForm.value.note = ''
  moduleMessage.value = '情绪打卡已保存。'
  await refreshModules()
}

async function submitTreehole() {
  if (!canPublishTreehole.value) {
    moduleMessage.value = readonlyReason.value
    return
  }
  await axios.post('/api/modules/treeholes/', {
    ...treeholeForm.value,
    is_anonymous: true,
  })
  treeholeForm.value.content = ''
  moduleMessage.value = '匿名树洞已发布。'
  await refreshModules()
}

async function submitAssessment() {
  if (!canWrite.value) {
    moduleMessage.value = readonlyReason.value
    return
  }
  const response = await axios.post('/api/modules/assessments/', {
    scale: assessmentForm.value.scale,
    answers: assessmentForm.value.answers.map((item) => Number(item)),
  })
  moduleMessage.value = `测评已提交：${response.data.scale_name}，得分 ${response.data.score}，风险等级 ${response.data.risk_level}。`
  await refreshModules()
}

async function submitAppointment() {
  if (!canWrite.value) {
    moduleMessage.value = readonlyReason.value
    return
  }
  await axios.post('/api/modules/appointments/', appointmentForm.value)
  appointmentForm.value.topic = ''
  appointmentForm.value.confidential_note = ''
  moduleMessage.value = '预约已提交，等待心理老师确认。'
  await refreshModules()
}

async function submitReply(postId) {
  if (!canReplyTreehole.value) {
    moduleMessage.value = readonlyReason.value
    return
  }
  const content = replyForms.value[postId]
  if (!content) return
  await axios.post(`/api/modules/treeholes/${postId}/reply/`, {
    content,
    responder_name: currentUser.value?.name,
    is_counselor_reply: currentRole.value === 'teacher',
  })
  replyForms.value[postId] = ''
  moduleMessage.value = '回应已发送。'
  await refreshModules()
}

async function adminDelete(url) {
  if (!canManage.value) return
  await axios.delete(url)
  moduleMessage.value = '管理员已删除该条数据。'
  await refreshModules()
}

async function adminPatch(url, payload) {
  if (!canManage.value) return
  await axios.patch(url, payload)
  moduleMessage.value = '管理员已更新该条数据。'
  await refreshModules()
}

async function permittedPatch(url, payload) {
  await axios.patch(url, payload)
  await refreshModules()
}

async function editTreehole(post) {
  const content = window.prompt('修改树洞内容', post.content)
  if (content !== null) {
    await adminPatch(`/api/treehole-posts/${post.id}/`, { content })
  }
}

function statusLabel(status) {
  const labels = {
    pending: '待确认',
    confirmed: '已确认',
    finished: '已完成',
    cancelled: '已取消',
  }
  return labels[status] || status || '未知状态'
}

function formatDateTime(value) {
  if (!value) return '时间待定'
  return String(value).replace('T', ' ').slice(0, 16)
}

async function changeAppointmentStatus(item, event) {
  const nextStatus = event.target.value
  if (!canOperateAppointments.value || nextStatus === item.status) return
  await permittedPatch(`/api/appointments/${item.id}/`, { status: nextStatus })
  moduleMessage.value = '预约状态已更新。'
}

function changeResourcePage(page) {
  resourcePage.value = Math.min(Math.max(1, page), resourceTotalPages.value)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function editAlert(alert) {
  if (!canManage.value) return
  await adminPatch(`/api/crisis-alerts/${alert.id}/`, { handled: !alert.handled })
}
</script>

<template>
  <div
    class="site-shell"
    :style="{ '--ink-x': inkX, '--ink-y': inkY, '--ink-active': inkActive, '--scroll-shift': scrollShift }"
    @pointerleave="handlePointerLeave"
  >
    <div class="ambient-layer" aria-hidden="true">
      <span class="ink-wash wash-one"></span>
      <span class="ink-wash wash-two"></span>
      <span class="ink-wash wash-three"></span>
    </div>
    <header class="site-header">
      <a class="brand" href="#/home" aria-label="心晴校园首页" @click.prevent="navigate('home')">
        <span class="brand-mark">
          <img :src="logoMark" alt="" />
        </span>
        <strong>心晴校园</strong>
      </a>

      <nav class="site-nav" aria-label="网站导航">
        <a href="#/home" @click.prevent="navigate('home')">首页</a>
        <a href="#/mood" @click.prevent="navigate('mood')">情绪打卡</a>
        <a href="#/treehole" @click.prevent="navigate('treehole')">匿名树洞</a>
        <a href="#/assessment" @click.prevent="navigate('assessment')">心理测评</a>
        <a href="#/appointment" @click.prevent="navigate('appointment')">咨询预约</a>
        <a href="#/resources" @click.prevent="navigate('resources')">心理资源</a>
        <a v-if="canViewAlerts" class="alert-nav-link" href="#/alerts" @click.prevent="navigate('alerts')">预警管理</a>
      </nav>

      <div class="auth-actions">
        <template v-if="currentUser">
          <span class="user-chip">{{ currentUser.name }}</span>
          <button class="text-button" type="button" @click="logoutAccount">退出</button>
        </template>
        <template v-else>
          <button class="text-button" type="button" @click="openAuth('login')">登录</button>
          <button class="solid-button" type="button" @click="openAuth('register')">注册</button>
        </template>
      </div>
    </header>

    <main v-if="currentPage === 'home'">
      <section id="home" class="hero-section scroll-follow follow-soft">
        <div class="hero-copy reveal-up">
          <span class="eyebrow">大学生心理支持与情绪表达平台</span>
          <h1>让每一次情绪表达<br />都能被温柔接住</h1>
          <p>
            面向高校学生、心理老师与管理者的一体化平台，整合情绪打卡、匿名倾诉、心理测评、咨询预约和风险预警。
          </p>
          <div class="hero-actions">
            <button class="solid-button large" type="button" @click="startExperience">立即体验</button>
            <button class="outline-button large" type="button" @click="scrollToModules">查看功能</button>
          </div>
          <div class="hero-metrics" aria-label="平台亮点">
            <div><strong>5+</strong><span>核心支持模块</span></div>
            <div><strong>24h</strong><span>紧急求助入口</span></div>
            <div><strong>2端</strong><span>学生与教师协同</span></div>
          </div>
        </div>

        <div class="hero-visual reveal-up delay-1">
          <img :src="heroImage" alt="大学心理支持平台场景图" />
          <div class="floating-card mood-card">
            <span>今日情绪</span>
            <strong>平静 7/10</strong>
            <div class="mini-bars"><i></i><i></i><i></i><i></i><i></i></div>
          </div>
          <div class="floating-card help-card">
            <span>推荐支持</span>
            <strong>三分钟呼吸放松</strong>
          </div>
        </div>
      </section>

      <section id="features" class="section feature-section scroll-follow follow-medium">
        <div class="section-heading align-left wide-heading">
          <span class="eyebrow">核心功能</span>
          <h2>从日常表达，到专业支持</h2>
          <p>平台不是单一的论坛或预约系统，而是一套围绕学生心理状态变化展开的支持路径。</p>
        </div>

        <div class="feature-grid">
          <article
            v-for="(feature, index) in features"
            :key="feature.title"
            :class="['feature-card', feature.accent]"
            tabindex="0"
            @click="navigate(['mood', 'treehole', 'assessment', 'appointment'][index])"
          >
            <span class="feature-stat">{{ feature.stat }}</span>
            <h3>{{ feature.title }}</h3>
            <button class="feature-subtitle" type="button">{{ feature.subtitle }}</button>
            <div class="feature-detail">
              <p>{{ feature.detail }}</p>
            </div>
            <p>{{ feature.desc }}</p>
          </article>
        </div>
      </section>

      <section id="scenes" class="section split-section scroll-follow follow-deep">
        <div class="section-heading align-left">
          <span class="eyebrow">使用场景</span>
          <h2>把校园心理服务变得更容易靠近</h2>
          <p>降低学生求助门槛，同时让心理老师拥有清晰、克制、可追踪的工作视图。</p>
        </div>

        <div class="scene-list">
          <article v-for="scene in scenes" :key="scene.label" class="scene-item">
            <span>{{ scene.label }}</span>
            <div>
              <h3>{{ scene.title }}</h3>
              <p>{{ scene.text }}</p>
            </div>
          </article>
        </div>
      </section>

      <section id="process" class="section process-section scroll-follow follow-medium">
        <div class="section-heading align-left wide-heading">
          <span class="eyebrow">支持流程</span>
          <h2>清晰的心理支持闭环</h2>
        </div>
        <div class="process-line">
          <div v-for="(step, index) in steps" :key="step" class="process-step">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <p>{{ step }}</p>
          </div>
        </div>
      </section>

      <section id="insights" class="section insight-section scroll-follow follow-medium">
        <div class="section-heading align-left wide-heading">
          <span class="eyebrow">心晴数据洞察</span>
          <h2>把心理状态转化为可理解的趋势</h2>
          <p>下方数据来自平台后端，用于呈现情绪变化、压力来源、预警数量和资源更新情况。</p>
        </div>

        <div v-if="loading" class="data-loading">正在从后端加载数据...</div>
        <template v-else>
          <div class="data-metrics">
            <article>
              <span>学生档案</span>
              <strong>{{ dashboard?.stats.students ?? 0 }}</strong>
            </article>
            <article>
              <span>咨询师</span>
              <strong>{{ dashboard?.stats.counselors ?? 0 }}</strong>
            </article>
            <article>
              <span>心理资源</span>
              <strong>{{ dashboard?.stats.articles ?? 0 }}</strong>
            </article>
            <article class="warning">
              <span>未处理预警</span>
              <strong>{{ dashboard?.stats.unhandled_alerts ?? 0 }}</strong>
            </article>
          </div>

          <div class="chart-grid">
            <article class="data-panel">
              <h3>情绪与睡眠趋势</h3>
              <div ref="trendChartRef" class="chart-box"></div>
            </article>
            <article class="data-panel">
              <h3>压力来源雷达图</h3>
              <div ref="pressureChartRef" class="chart-box"></div>
            </article>
          </div>
        </template>
      </section>

      <section id="support" class="section support-section scroll-follow follow-deep">
        <div class="section-heading align-left wide-heading">
          <span class="eyebrow">专业对接</span>
          <h2>基于学生偏好与压力来源推荐咨询师</h2>
          <p>后端根据学生压力来源、关注主题与咨询师擅长领域计算匹配分，后续可替换为更完整的推荐算法。</p>
        </div>

        <div class="compact-list support-list">
          <article v-for="counselor in homeCounselors" :key="counselor.id" class="counselor-row" @click="navigate('appointment')">
            <span class="counselor-avatar small" :style="{ background: counselor.avatar_color }">{{ counselor.name.slice(0, 1) }}</span>
            <div class="compact-main">
              <h3>{{ counselor.name }}</h3>
              <p>{{ counselor.title }}</p>
            </div>
            <div class="tag-list compact-tags">
              <span v-for="tag in counselor.specialties.slice(0, 3)" :key="tag">{{ tag }}</span>
            </div>
            <strong>{{ counselor.match_score }}%</strong>
          </article>
        </div>
        <button class="more-link" type="button" @click="navigate('appointment')">&gt;&gt;&gt;更多</button>
      </section>

      <section id="resources" class="section resource-section scroll-follow follow-medium">
        <div class="section-heading align-left wide-heading">
          <span class="eyebrow">心理资源</span>
          <h2>科普文章与自助干预内容动态更新</h2>
        </div>

        <div class="compact-list resource-list">
          <article v-for="article in homeArticles" :key="article.id" class="resource-row" @click="openArticle(article)">
            <span>{{ article.category }} · {{ article.source }}</span>
            <h3>{{ article.title }}</h3>
            <p>{{ article.summary }}</p>
            <div class="tag-list compact-tags">
              <span v-for="tag in article.tags.slice(0, 3)" :key="tag">{{ tag }}</span>
            </div>
          </article>
        </div>
        <button class="more-link" type="button" @click="navigate('resources')">&gt;&gt;&gt;更多</button>
      </section>

      <section id="modules" class="section module-section scroll-follow follow-deep">
        <div class="section-heading align-left wide-heading">
          <span class="eyebrow">功能简介</span>
          <h2>按模块进入对应功能页</h2>
          <p>首页只保留功能说明和入口。点击任一简介卡片后进入对应功能页，再按当前角色进行浏览、提交或管理。</p>
        </div>

        <div class="module-intro-grid">
          <article
            v-for="intro in moduleIntros"
            :key="intro.page"
            class="module-intro-card"
            tabindex="0"
            @click="navigate(intro.page)"
            @keydown.enter="navigate(intro.page)"
          >
            <span>{{ intro.stat }}</span>
            <h3>{{ intro.title }}</h3>
            <p>{{ intro.text }}</p>
            <div class="tag-list">
              <span v-for="point in intro.points" :key="point">{{ point }}</span>
            </div>
            <button class="text-button intro-link" type="button">进入{{ intro.title }}</button>
          </article>
        </div>
      </section>

      <section v-if="!currentUser" id="contact" class="cta-section scroll-follow follow-deep">
        <div>
          <span class="eyebrow">开始使用</span>
          <h2>进入平台，建立属于校园的心理支持空间</h2>
          <p>前端页面完成后，可继续接入 Django 后端，实现用户、打卡、树洞、预约、测评与预警数据管理。</p>
        </div>
        <div class="cta-actions">
          <button class="solid-button large" type="button" @click="openAuth('login')">登录平台</button>
          <button class="outline-button large" type="button" @click="openAuth('register')">创建账号</button>
        </div>
      </section>
    </main>

    <main v-else class="standalone-page">
      <section class="page-hero">
        <button class="text-button" type="button" @click="navigate('home')">返回首页</button>
        <span class="eyebrow">{{ pageTitles[currentPage] }}</span>
        <h1>{{ pageTitles[currentPage] }}</h1>
      </section>

      <section v-if="currentPage === 'register'" class="register-page module-panel page-panel">
        <div class="register-heading">
          <span class="eyebrow">学生档案</span>
          <h2>创建账号并完善基础信息</h2>
          <p>这些信息会写入学生档案，用于后续情绪记录、测评、咨询预约和资源推荐。</p>
        </div>

        <form class="register-form" @submit.prevent="submitRegister">
          <div class="registration-grid">
            <label>账号<input v-model.trim="authForm.username" placeholder="用于登录的账号" required /></label>
            <label>姓名<input v-model.trim="authForm.name" placeholder="真实姓名或常用称呼" /></label>
            <label>邮箱<input v-model.trim="authForm.email" type="email" placeholder="用于联系和通知" /></label>
            <label>角色
              <select v-model="authForm.role">
                <option>学生</option>
                <option>心理老师</option>
                <option>管理员</option>
              </select>
            </label>
            <label>密码<input v-model="authForm.password" placeholder="请输入密码" type="password" required /></label>
            <label>确认密码<input v-model="authForm.confirmPassword" placeholder="再次输入密码" type="password" required /></label>

            <template v-if="authForm.role === '学生'">
              <label>学号<input v-model.trim="authForm.studentNo" placeholder="学生档案唯一编号" required /></label>
              <label>学院<input v-model.trim="authForm.college" placeholder="所在学院" /></label>
              <label>年级<input v-model.trim="authForm.grade" placeholder="例如：2023级" /></label>
              <label>压力来源<input v-model="authForm.pressureSources" placeholder="用逗号分隔，如学业、人际、睡眠" /></label>
              <label class="full">关注主题<input v-model="authForm.preferredTopics" placeholder="用逗号分隔，如焦虑调节、时间管理、咨询预约" /></label>
              <label class="consent full">
                <input v-model="authForm.privacyConsent" type="checkbox" />
                <span>同意平台在校内心理支持场景下保存并使用以上信息</span>
              </label>
            </template>
          </div>

          <p v-if="authMessage" class="auth-message">{{ authMessage }}</p>
          <div class="register-actions">
            <button class="solid-button large" type="submit" :disabled="authSubmitting">
              {{ authSubmitting ? '提交中...' : '完成注册' }}
            </button>
            <button class="text-button" type="button" @click="openAuth('login')">已有账号，去登录</button>
          </div>
        </form>
      </section>

      <section v-if="currentPage === 'details'" class="detail-page">
        <article class="detail-overview module-panel">
          <span class="eyebrow">平台说明</span>
          <h2>围绕“表达、识别、对接、关怀”的心理支持闭环</h2>
          <p>
            平台面向学生、心理教师和管理员提供分层功能。学生可以记录和提交数据；教师侧重查询、理解和跟进；
            管理员负责维护数据、处理预警和管理内容。
          </p>
        </article>

        <div class="detail-grid">
          <article v-for="item in moduleDetails" :key="item.page" class="detail-card">
            <div class="detail-card-head">
              <div>
                <span>{{ item.title }}</span>
                <h3>{{ item.summary }}</h3>
              </div>
              <button class="text-button" type="button" @click="navigate(item.page)">进入模块</button>
            </div>

            <div class="detail-columns">
              <section>
                <h4>学生可以做什么</h4>
                <ul>
                  <li v-for="text in item.student" :key="text">{{ text }}</li>
                </ul>
              </section>
              <section>
                <h4>教师可以了解什么</h4>
                <ul>
                  <li v-for="text in item.teacher" :key="text">{{ text }}</li>
                </ul>
              </section>
              <section>
                <h4>涉及数据</h4>
                <div class="tag-list">
                  <span v-for="text in item.data" :key="text">{{ text }}</span>
                </div>
              </section>
            </div>
          </article>
        </div>
      </section>

      <section v-if="currentPage === 'mood'" class="module-panel page-panel">
        <h3>情绪打卡记录</h3>
        <form v-if="canWrite" class="module-form" @submit.prevent="submitMood">
          <label>今日情绪<input v-model="moodForm.mood" /></label>
          <label>情绪强度<input v-model="moodForm.intensity" type="range" min="1" max="10" /></label>
          <label>睡眠质量<input v-model="moodForm.sleep_quality" type="range" min="1" max="10" /></label>
          <label>压力来源<input v-model="moodForm.pressure_sources" /></label>
          <label class="full">日记<textarea v-model="moodForm.note"></textarea></label>
          <button class="solid-button large" type="submit">保存打卡</button>
        </form>
        <p v-if="moduleMessage" class="module-message">{{ moduleMessage }}</p>
        <div class="module-list">
          <article v-for="item in moduleData?.moods" :key="item.id">
            <strong>{{ item.student_name }}：{{ item.mood }} {{ item.intensity }}/10</strong>
            <p>{{ item.note || '暂无日记内容' }}</p>
            <button v-if="canManage" class="danger-button" type="button" @click="adminDelete(`/api/mood-entries/${item.id}/`)">删除</button>
          </article>
        </div>
      </section>

      <section v-if="currentPage === 'treehole'" class="module-panel page-panel">
        <h3>匿名树洞</h3>
        <form v-if="canPublishTreehole" class="module-form" @submit.prevent="submitTreehole">
          <label>分类
            <select v-model="treeholeForm.category">
              <option value="study">学业压力</option>
              <option value="relationship">人际关系</option>
              <option value="family">家庭关系</option>
              <option value="growth">自我成长</option>
              <option value="other">其他</option>
            </select>
          </label>
          <label>情绪标签<input v-model="treeholeForm.mood_tag" /></label>
          <label class="full">匿名内容<textarea v-model="treeholeForm.content" required></textarea></label>
          <button class="solid-button large" type="submit">发布树洞</button>
        </form>
        <p v-if="moduleMessage" class="module-message">{{ moduleMessage }}</p>
        <div class="treehole-list">
          <article v-for="post in moduleData?.treeholes" :key="post.id" class="treehole-post">
            <span>{{ post.student_name }} · {{ post.mood_tag || '未标记' }}</span>
            <p>{{ post.content }}</p>
            <div class="reply-list">
              <p v-for="reply in post.replies" :key="reply.id">{{ reply.responder_name }}：{{ reply.content }}</p>
            </div>
            <form v-if="canReplyTreehole" class="reply-form" @submit.prevent="submitReply(post.id)">
              <input v-model="replyForms[post.id]" placeholder="写一句温和回应" />
              <button type="submit">回应</button>
            </form>
            <div v-if="canManage" class="admin-actions">
              <button type="button" @click="editTreehole(post)">编辑</button>
              <button class="danger-button" type="button" @click="adminDelete(`/api/treehole-posts/${post.id}/`)">删除</button>
            </div>
          </article>
        </div>
      </section>

      <section v-if="currentPage === 'assessment'" class="module-panel page-panel">
        <h3>心理测评</h3>
        <form v-if="canWrite" class="module-form" @submit.prevent="submitAssessment">
          <label class="full">选择量表
            <select v-model="assessmentForm.scale">
              <option v-for="scale in moduleData?.scales" :key="scale.id" :value="scale.id">{{ scale.name }}</option>
            </select>
          </label>
          <div class="question-list full">
            <label v-for="(question, index) in moduleData?.scales?.find((item) => item.id == assessmentForm.scale)?.questions" :key="question.title">
              {{ question.title }}
              <input v-model="assessmentForm.answers[index]" type="range" min="0" max="10" />
            </label>
          </div>
          <button class="solid-button large" type="submit">提交测评</button>
        </form>
        <p v-if="moduleMessage" class="module-message">{{ moduleMessage }}</p>
        <div class="module-list">
          <article v-for="record in moduleData?.records" :key="record.id">
            <strong>{{ record.student_name }}：{{ record.scale_name }} {{ record.score }} 分</strong>
            <p>{{ record.suggestion }}</p>
            <button v-if="canManage" class="danger-button" type="button" @click="adminDelete(`/api/assessment-records/${record.id}/`)">删除</button>
          </article>
        </div>
      </section>

      <section v-if="currentPage === 'appointment'" class="module-panel page-panel">
        <h3>咨询预约</h3>
        <div class="appointment-board appointment-info-board">
          <h4>同学预约信息</h4>
          <div v-if="visibleAppointments.length" class="appointment-strip">
            <article v-for="item in visibleAppointments" :key="`strip-${item.id}`">
              <strong>{{ item.student_name }}</strong>
              <span>{{ item.counselor_name }}</span>
              <div class="tag-list appointment-tags">
                <span v-for="tag in (item.counselor_specialties || []).slice(0, 3)" :key="tag">{{ tag }}</span>
              </div>
              <span>{{ item.topic }}</span>
              <span>{{ formatDateTime(item.scheduled_at) }}</span>
              <label v-if="canOperateAppointments" class="status-select compact-status">
                <select :value="item.status" @change="changeAppointmentStatus(item, $event)">
                  <option value="pending">待确认</option>
                  <option value="confirmed">已确认</option>
                  <option value="finished">已完成</option>
                  <option value="cancelled">已取消</option>
                </select>
              </label>
              <em v-else>{{ statusLabel(item.status) }}</em>
              <button v-if="canManage" class="danger-button appointment-delete" type="button" @click="adminDelete(`/api/appointments/${item.id}/`)">删除</button>
            </article>
          </div>
          <p v-else class="empty-state">暂无可展示的预约信息。</p>
        </div>

        <div v-if="canWrite" class="appointment-board appointment-form-board">
          <h4>学生咨询预约表</h4>
          <form class="module-form" @submit.prevent="submitAppointment">
            <label>咨询师
              <select v-model="appointmentForm.counselor">
                <option v-for="item in moduleData?.counselors" :key="item.id" :value="item.id">{{ item.name }} · {{ item.title }}</option>
              </select>
            </label>
            <label>预约时间<input v-model="appointmentForm.scheduled_at" type="datetime-local" /></label>
            <label class="full">咨询主题<input v-model="appointmentForm.topic" required /></label>
            <label class="full">保密备注<textarea v-model="appointmentForm.confidential_note"></textarea></label>
            <button class="solid-button large" type="submit">提交预约</button>
          </form>
          <p v-if="moduleMessage" class="module-message">{{ moduleMessage }}</p>
        </div>
      </section>

      <section v-if="currentPage === 'resources'" class="module-panel page-panel">
        <h3>心理资源</h3>
        <div class="topic-resource-list">
          <article v-for="article in pagedArticles" :key="article.id" class="topic-resource-item">
            <h3 class="article-title-link" @click="openArticle(article)">{{ article.title }}</h3>
            <span>{{ article.category }} · {{ article.source }}</span>
            <p>{{ article.summary }}</p>
            <div class="tag-list compact-tags">
              <span v-for="tag in article.tags.slice(0, 4)" :key="tag">{{ tag }}</span>
            </div>
            <button v-if="canManage" class="danger-button" type="button" @click.stop="adminDelete(`/api/articles/${article.id}/`)">删除</button>
          </article>
        </div>
        <div class="pagination-bar">
          <button type="button" :disabled="resourcePage <= 1" @click="changeResourcePage(resourcePage - 1)">上一页</button>
          <span>第 {{ resourcePage }} / {{ resourceTotalPages }} 页 · 共 {{ articles.length }} 篇</span>
          <button type="button" :disabled="resourcePage >= resourceTotalPages" @click="changeResourcePage(resourcePage + 1)">下一页</button>
        </div>
      </section>

      <section v-if="currentPage === 'article'" class="article-detail module-panel page-panel">
        <template v-if="currentArticle">
          <span class="eyebrow">{{ currentArticle.category }} · {{ currentArticle.source }}</span>
          <h2>{{ currentArticle.title }}</h2>
          <p class="article-summary">{{ currentArticle.summary }}</p>
          <div class="tag-list">
            <span v-for="tag in currentArticle.tags" :key="tag">{{ tag }}</span>
          </div>
          <article class="article-content">
            <p v-for="paragraph in currentArticle.content.split('\n').filter(Boolean)" :key="paragraph">{{ paragraph }}</p>
          </article>
          <div class="article-meta">
            <span v-if="currentArticle.fetched_at">抓取时间：{{ currentArticle.fetched_at }}</span>
            <a v-if="currentArticle.external_url" :href="currentArticle.external_url" target="_blank" rel="noreferrer">查看权威原文</a>
          </div>
        </template>
        <template v-else>
          <h2>未找到文章</h2>
          <button class="outline-button large" type="button" @click="navigate('resources')">返回心理资源</button>
        </template>
      </section>

      <section v-if="currentPage === 'alerts' && canViewAlerts" class="module-panel page-panel alerts-panel">
        <h3>危机预警</h3>
        <div class="module-list">
          <article v-for="alert in moduleData?.alerts" :key="alert.id" class="alert-card">
            <strong>{{ alert.student_name }} · {{ alert.level }}</strong>
            <p>{{ alert.trigger }}</p>
            <div v-if="canManage" class="admin-actions">
              <button type="button" @click="editAlert(alert)">{{ alert.handled ? '标记未处理' : '标记已处理' }}</button>
              <button class="danger-button" type="button" @click="adminDelete(`/api/crisis-alerts/${alert.id}/`)">删除</button>
            </div>
          </article>
        </div>
        <a v-if="canManage" class="outline-link admin-link" href="http://127.0.0.1:8000/admin/" target="_blank" rel="noreferrer">进入 Django 后台管理</a>
      </section>
    </main>

    <footer v-if="currentPage === 'home'" class="site-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <img :src="logoMark" alt="" />
          <div>
            <strong>心晴校园</strong>
            <span>心理支持与情绪表达平台</span>
          </div>
        </div>

        <div class="footer-content">
          <nav class="footer-links" aria-label="底部链接">
            <a href="#home">首页</a>
            <a href="#features">功能服务</a>
            <a href="#scenes">使用场景</a>
            <a href="#contact">联系我们</a>
            <a href="#contact">加入我们</a>
          </nav>

          <p>
            健康提示：平台内容用于心理健康教育、自我记录和校园支持服务，不替代专业医疗诊断。如出现持续强烈痛苦、
            自伤想法或紧急风险，请立即联系学校心理中心、辅导员或当地紧急援助渠道。
          </p>
          <p>
            服务说明：情绪打卡、匿名表达、心理测评与咨询预约数据仅用于校园心理支持流程；平台倡导尊重、保密、及时响应的求助环境。
          </p>
          <p>
            所属学校：北京城市学院 ｜ 联系邮箱：1751551811@qq.com ｜ 联系电话：18513020539；13107209820
          </p>
          <p>
            服务时间：工作日 08:00-20:00 ｜ 紧急支持：请优先联系学校值班老师或当地紧急援助渠道。
          </p>

          <div class="footer-badges" aria-label="平台服务标签">
            <span>隐私保护</span>
            <span>匿名表达</span>
            <span>咨询预约</span>
            <span>风险提醒</span>
          </div>
        </div>
      </div>
    </footer>

    <div v-if="showAuth" class="modal-backdrop" @click.self="showAuth = false">
      <section class="auth-modal" role="dialog" aria-modal="true" aria-label="登录注册">
        <button class="modal-close" type="button" aria-label="关闭" @click="showAuth = false">×</button>
        <div class="auth-tabs">
          <button class="active" type="button">登录</button>
          <button type="button" @click="openAuth('register')">注册</button>
        </div>
        <h2>欢迎回来</h2>
        <p>登录后进入学生端或教师端。</p>
        <form class="auth-form" @submit.prevent="submitAuth">
          <input v-model.trim="authForm.username" placeholder="学号 / 工号 / 邮箱" required />
          <input v-model="authForm.password" placeholder="密码" type="password" required />
          <p v-if="authMessage" class="auth-message">{{ authMessage }}</p>
          <button class="solid-button large" type="submit" :disabled="authSubmitting">
            {{ authSubmitting ? '提交中...' : '登录' }}
          </button>
        </form>
      </section>
    </div>
  </div>
</template>
