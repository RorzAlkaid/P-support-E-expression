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
const insightData = ref(null)
const insightLoading = ref(false)
const insightMessage = ref('')
const counselors = ref([])
const articles = ref([])
const tags = ref([])
const counselorSearch = ref('')
const resourceSearch = ref('')
const counselorPage = ref(1)
const counselorPageSize = 4
const tagDrafts = ref({})
const tagSuggestionMessage = ref('')
const tagPopup = ref({
  visible: false,
  x: 0,
  y: 0,
  targetType: '',
  targetId: null,
  showAll: false,
  newTag: '',
})
const trendChartRef = ref(null)
const pressureChartRef = ref(null)
const riskChartRef = ref(null)
const appointmentChartRef = ref(null)
const appointmentTimeInput = ref(null)
let trendChart = null
let pressureChart = null
let riskChart = null
let appointmentChart = null
let chartResizeObserver = null
let chartVisibilityObserver = null
let scrollRevealObserver = null
let chartRenderTimer = null
let chartRenderAttempts = 0
const maxChartRenderAttempts = 12
const currentUser = ref(null)
const initialHashParts = window.location.hash?.replace('#/', '').split('/') || ['home']
const currentPage = ref(
  (initialHashParts[0] === 'treehole' && initialHashParts[1]) ? 'treehole-detail' :
  (initialHashParts[0] || 'home')
)
const authReady = ref(false)
const authSubmitting = ref(false)
const authMessage = ref('')
const moduleData = ref(null)
const moduleMessage = ref('')
const aiChatInput = ref('')
const aiChatSending = ref(false)
const aiChatMessage = ref('')
const aiChatWindowRef = ref(null)
const aiSpeechSupported = ref(false)
const aiSpeechListening = ref(false)
const aiSpeechMessage = ref('')
const aiConfigLoading = ref(false)
const aiConfigSaving = ref(false)
const aiConfigMessage = ref('')
const aiConfigForm = ref({
  enabled: true,
  provider: 'openai',
  api_key: '',
  api_key_masked: '',
  api_url: 'https://api.openai.com/v1/chat/completions',
  model: 'gpt-4o-mini',
  auto_detect_model: false,
  timeout: 30,
  configured: false,
  source: '',
})
const aiChatMessages = ref([
  {
    role: 'assistant',
    content: '你好，我是平台里的 AI 倾听助手。你可以把此刻的压力、情绪或困扰告诉我，我们先一起把它慢慢理清。',
  },
])

const aiProviderPresets = [
  {
    id: 'openai',
    name: 'OpenAI',
    api_url: 'https://api.openai.com/v1/chat/completions',
    model: 'gpt-4o-mini',
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    api_url: 'https://api.deepseek.com/chat/completions',
    model: 'deepseek-v4-flash',
  },
]
const heartWallVisible = ref(false)
const heartWallKey = ref(0)
let heartWallTimer = null
let invitationCopyToastTimer = null
let scrollMotionFrame = null
let pendingFullPageReload = false
let aiSpeechRecognition = null
let aiSpeechSilenceTimer = null
const selectedAlertDetail = ref(null)
const alertDetailLoading = ref(false)
const alertDetailMessage = ref('')
const currentArticleId = ref(initialHashParts[0] === 'article' ? initialHashParts[1] : null)
const currentAlertId = ref(initialHashParts[0] === 'alert-detail' ? initialHashParts[1] : null)
const currentTreeholeId = ref(initialHashParts[0] === 'treehole' ? initialHashParts[1] : null)
const activeModule = ref('mood')
const resourcePage = ref(1)
const resourcePageSize = 24
const moodPage = ref(1)
const treeholePage = ref(1)
const recordPage = ref(1)
const alertPage = ref(1)
const listPageSize = 8
const counselorCreateForm = ref({
  student_id: null,
  name: '',
  title: '心理教师',
  specialties: '',
  qualifications: '',
  available_slots: '',
  avatar_color: '#d85d73',
})
const counselorCreateMessage = ref('')
const counselorCreateLoading = ref(false)
const studentList = ref([])
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
const teacherProfileForm = ref({
  name: '',
  title: '心理教师',
  specialties: '',
  qualifications: '',
  available_slots: '',
})
const profileForm = ref({
  name: '',
  email: '',
  college: '',
  grade: '',
  pressure_sources: '',
  preferred_topics: '',
  privacy_consent: false,
  title: '',
  specialties: '',
  qualifications: '',
  available_slots: '',
})
const profileMessage = ref('')
const invitationDrafts = ref({
  teacher: '',
  admin: '',
})
const invitationLocks = ref({
  teacher: false,
  admin: false,
})
const invitationCopyToast = ref({
  visible: false,
  x: 0,
  y: 0,
})
const replyForms = ref({})
const authForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  role: '学生',
  invitationCode: '',
  name: '',
  email: '',
  studentNo: '',
  college: '',
  grade: '',
  pressureSources: '',
  preferredTopics: '',
  privacyConsent: false,
  teacherTitle: '',
  teacherSpecialties: '',
  teacherQualifications: '',
})

const roleLabels = {
  student: '学生',
  teacher: '教师',
  admin: '管理员',
}

const roleRegisterLabels = {
  student: '学生注册',
  teacher: '教师注册',
  admin: '管理员注册',
}

const roleLoginLabels = {
  student: '学生登录',
  teacher: '教师登录',
  admin: '管理员登录',
}

const roleFormValues = {
  student: '学生',
  teacher: '心理老师',
  admin: '管理员',
}

const pageTitles = {
  home: '首页',
  register: '账号注册',
  profile: '个人资料',
  details: '平台详情',
  article: '文章详情',
  'ai-chat': 'AI 倾听对话',
  mood: '情绪打卡',
  treehole: '匿名树洞',
  assessment: '心理测评',
  appointment: '咨询预约',
  resources: '心理资源',
  alerts: '预警管理',
  insights: '数据洞察',
  'alert-detail': '预警学生详情',
  'treehole-detail': '树洞详情',
}

const pageAccessRules = {
  profile: { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '个人资料' },
  mood: { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '情绪打卡' },
  treehole: { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '匿名树洞' },
  assessment: { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '心理测评' },
  appointment: { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '咨询预约' },
  resources: { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '心理资源' },
  article: { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '文章详情' },
  'ai-chat': { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: 'AI 倾听对话' },
  insights: { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '数据洞察' },
  alerts: { roles: ['teacher', 'admin'], loginRequired: true, label: '预警管理' },
  'alert-detail': { roles: ['teacher', 'admin'], loginRequired: true, label: '预警学生详情' },
  'treehole-detail': { roles: ['student', 'teacher', 'admin'], loginRequired: true, label: '树洞详情' },
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
    page: 'ai-chat',
    title: 'AI 倾听对话',
    stat: '实时陪伴',
    text: '接入大模型对话能力，帮助学生在压力、焦虑或低落时获得即时倾听、情绪梳理和自助建议。',
    points: ['即时对话', '情绪疏导', '风险提醒'],
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
const activeAuthRole = computed(() => {
  if (authForm.value.role === '管理员') return 'admin'
  if (authForm.value.role === '心理老师' || authForm.value.role === '教师') return 'teacher'
  return 'student'
})
const activeAuthRoleLabel = computed(() => roleLabels[activeAuthRole.value])
const activeLoginTitle = computed(() => roleLoginLabels[activeAuthRole.value])
const activeRegisterTitle = computed(() => roleRegisterLabels[activeAuthRole.value])
const targetInvitationRoles = computed(() => {
  if (currentRole.value === 'admin') {
    return [
      { role: 'teacher', label: '教师邀请码' },
      { role: 'admin', label: '管理员邀请码' },
    ]
  }
  if (currentRole.value === 'teacher') {
    return [{ role: 'teacher', label: '教师邀请码' }]
  }
  return []
})
const minAppointmentDateTime = computed(() => formatDateTimeInput(new Date()))
const canWrite = computed(() => ['student', 'admin'].includes(currentRole.value))
const canUseAiChat = computed(() => ['student', 'teacher', 'admin'].includes(currentRole.value))
const canManage = computed(() => currentRole.value === 'admin')
const adminUrl = computed(() => import.meta.env.DEV ? 'http://127.0.0.1:8000/admin/' : '/admin/')
const canViewAlerts = computed(() => ['teacher', 'admin'].includes(currentRole.value))
const canViewInsights = computed(() => true)
const canDownloadInsights = computed(() => ['teacher', 'admin'].includes(currentRole.value))
const canOperateAppointments = computed(() => ['teacher', 'admin'].includes(currentRole.value))
const canPublishTreehole = computed(() => ['student', 'admin'].includes(currentRole.value))
const canReplyTreehole = computed(() => ['student', 'teacher', 'admin'].includes(currentRole.value))
const studentsWithoutCounselor = computed(() => {
  const counselorUserIds = new Set(
    moduleData.value?.counselors?.map((c) => c.user).filter(Boolean) || []
  )
  return (studentList.value || []).filter(
    (s) => !counselorUserIds.has(s.user_id)
  )
})
const currentArticle = computed(() => articles.value.find((item) => String(item.id) === String(currentArticleId.value)))
const currentTreehole = computed(() => allTreeholes.value.find((item) => String(item.id) === String(currentTreeholeId.value)))
const homeCounselors = computed(() => counselors.value.slice(0, 6))
const homeArticles = computed(() => articles.value.slice(0, 6))
const recommendedCounselors = computed(() => filterByKeyword(moduleData.value?.counselors || counselors.value, counselorSearch.value, ['name', 'title', 'qualifications', 'specialties', 'related_tags']))
const counselorTotalPages = computed(() => Math.max(1, Math.ceil(recommendedCounselors.value.length / counselorPageSize)))
const pagedRecommendedCounselors = computed(() => {
  const page = Math.min(counselorPage.value, counselorTotalPages.value)
  const start = (page - 1) * counselorPageSize
  return recommendedCounselors.value.slice(start, start + counselorPageSize)
})
const filteredArticles = computed(() => filterByKeyword(articles.value, resourceSearch.value, ['title', 'source', 'category', 'summary', 'tags', 'related_tags']))
const resourceTotalPages = computed(() => Math.max(1, Math.ceil(filteredArticles.value.length / resourcePageSize)))
const pagedArticles = computed(() => {
  const page = Math.min(resourcePage.value, resourceTotalPages.value)
  const start = (page - 1) * resourcePageSize
  return filteredArticles.value.slice(start, start + resourcePageSize)
})
const visibleAppointments = computed(() => {
  const appointments = moduleData.value?.appointments || []
  if (['teacher', 'admin'].includes(currentRole.value)) return appointments
  return appointments.filter((item) => !['pending', 'cancelled'].includes(item.status))
})
const recentAppointments = computed(() => visibleAppointments.value.slice(0, 5))
const hasMoreAppointments = computed(() => visibleAppointments.value.length > 5)

const moodItems = computed(() => moduleData.value?.moods || [])
const moodTotalPages = computed(() => Math.max(1, Math.ceil(moodItems.value.length / listPageSize)))
const pagedMoods = computed(() => {
  const page = Math.min(moodPage.value, moodTotalPages.value)
  return moodItems.value.slice((page - 1) * listPageSize, page * listPageSize)
})

const allTreeholes = ref([])
const treeholeLoading = ref(false)
const treeholeItems = computed(() => allTreeholes.value)
const treeholeTotalPages = computed(() => Math.max(1, Math.ceil(treeholeItems.value.length / listPageSize)))
const pagedTreeholes = computed(() => {
  const page = Math.min(treeholePage.value, treeholeTotalPages.value)
  return treeholeItems.value.slice((page - 1) * listPageSize, page * listPageSize)
})

const recordItems = computed(() => moduleData.value?.records || [])
const recordTotalPages = computed(() => Math.max(1, Math.ceil(recordItems.value.length / listPageSize)))
const pagedRecords = computed(() => {
  const page = Math.min(recordPage.value, recordTotalPages.value)
  return recordItems.value.slice((page - 1) * listPageSize, page * listPageSize)
})

const alertItems = computed(() => moduleData.value?.alerts || [])
const alertTotalPages = computed(() => Math.max(1, Math.ceil(alertItems.value.length / listPageSize)))
const pagedAlerts = computed(() => {
  const page = Math.min(alertPage.value, alertTotalPages.value)
  return alertItems.value.slice((page - 1) * listPageSize, page * listPageSize)
})

function filterByKeyword(items, keyword, fields) {
  const normalized = String(keyword || '').trim().toLowerCase()
  if (!normalized) return items
  return items.filter((item) => {
    const text = fields.map((field) => {
      const value = item?.[field]
      return Array.isArray(value) ? value.join(' ') : value
    }).join(' ').toLowerCase()
    return text.includes(normalized)
  })
}

function tagEditorKey(targetType, targetId) {
  return `${targetType}-${targetId}`
}

function availableUnusedTags(currentTags = []) {
  const used = new Set((currentTags || []).map((tag) => String(tag).trim().toLowerCase()).filter(Boolean))
  return tags.value.filter((tag) => {
    const name = String(tag.name || '').trim()
    return name && tag.is_active !== false && !used.has(name.toLowerCase())
  })
}

const popupAvailableTags = computed(() => {
  if (!tagPopup.value.targetType || !tagPopup.value.targetId) return []
  const targetType = tagPopup.value.targetType
  const targetId = tagPopup.value.targetId
  let currentTags = []
  if (targetType === 'counselor') {
    const counselor = (moduleData.value?.counselors || counselors.value).find((c) => c.id === targetId)
    currentTags = counselor?.specialties || []
  } else if (targetType === 'article') {
    const article = articles.value.find((a) => a.id === targetId)
    currentTags = article?.tags || []
  }
  return availableUnusedTags(currentTags)
})

const popupVisibleTags = computed(() => {
  const all = popupAvailableTags.value
  if (tagPopup.value.showAll || all.length <= 5) return all
  return all.slice(0, 5)
})

const popupHasMoreTags = computed(() => {
  return popupAvailableTags.value.length > 5 && !tagPopup.value.showAll
})

function openTagPopup(event, targetType, targetId) {
  const rect = event.currentTarget.getBoundingClientRect()
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0
  const popupWidth = 260
  let left = rect.left
  if (left + popupWidth > viewportWidth - 12) {
    left = Math.max(8, viewportWidth - popupWidth - 12)
  }
  tagPopup.value = {
    visible: true,
    x: left,
    y: rect.bottom + 6,
    targetType,
    targetId,
    showAll: false,
    newTag: '',
  }
}

function closeTagPopup() {
  tagPopup.value.visible = false
}

async function selectExistingTag(tagName) {
  if (!tagPopup.value.targetType || !tagPopup.value.targetId) return
  await applyTagToTarget(tagPopup.value.targetType, tagPopup.value.targetId, tagName)
  closeTagPopup()
}

async function submitPopupNewTag() {
  const tagName = String(tagPopup.value.newTag || '').trim()
  if (!tagName || !tagPopup.value.targetType || !tagPopup.value.targetId) return
  await applyTagToTarget(tagPopup.value.targetType, tagPopup.value.targetId, tagName)
  closeTagPopup()
}

async function applyTagToTarget(targetType, targetId, tagName) {
  try {
    const response = await axios.post('/api/tag-suggestions/', {
      target_type: targetType,
      target_id: targetId,
      tag_name: tagName,
    })
    tagSuggestionMessage.value = response.data.status === 'applied'
      ? '标签已添加。'
      : '新标签已提交，等待教师或管理员审核。'
    await refreshModules()
    const [articlesRes, tagsRes] = await Promise.all([
      axios.get('/api/articles/'),
      axios.get('/api/tags/'),
    ])
    articles.value = articlesRes.data.results ?? articlesRes.data
    tags.value = tagsRes.data.results ?? tagsRes.data
  } catch (error) {
    tagSuggestionMessage.value = error.response?.data?.detail || '标签提交失败。'
  }
}

function changeCounselorPage(page) {
  counselorPage.value = Math.min(Math.max(1, page), counselorTotalPages.value)
}
const selectedStudentProfile = computed(() => selectedAlertDetail.value?.student || null)
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
  scheduleScrollMotion()
}

function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value))
}

function updateScrollMotion() {
  scrollMotionFrame = null
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 800
  const focusLine = viewportHeight * 0.52
  const activeDistance = Math.max(viewportHeight * 0.72, 420)

  document.querySelectorAll('.scroll-converge').forEach((el) => {
    const rect = el.getBoundingClientRect()
    const center = rect.top + rect.height / 2
    const distance = Math.abs(center - focusLine)
    const gather = clamp(1 - distance / activeDistance)
    const eased = 1 - Math.pow(1 - gather, 3)
    const scatterX = Number(el.dataset.scatterX || 0)
    const motionX = scatterX * (1 - eased)

    el.style.setProperty('--motion-x', `${motionX.toFixed(2)}px`)
    el.style.setProperty('--motion-scale', (0.94 + eased * 0.06).toFixed(3))
    el.style.setProperty('--motion-opacity', (0.42 + eased * 0.58).toFixed(3))
    el.style.setProperty('--motion-depth', eased.toFixed(3))
  })
}

function scheduleScrollMotion() {
  if (scrollMotionFrame) return
  scrollMotionFrame = window.requestAnimationFrame(updateScrollMotion)
}

function motionAttrs(index, total = 4, distance = 96) {
  const center = (total - 1) / 2
  const offset = index - center
  const direction = offset === 0 ? (index % 2 === 0 ? -1 : 1) : Math.sign(offset)
  const scatterX = direction * (distance + Math.abs(offset) * distance * 0.38)
  return {
    'data-scatter-x': scatterX.toFixed(0),
  }
}

function showHeartWall() {
  heartWallVisible.value = false
  heartWallKey.value += 1
  window.clearTimeout(heartWallTimer)
  requestAnimationFrame(() => {
    heartWallVisible.value = true
    heartWallTimer = window.setTimeout(() => {
      heartWallVisible.value = false
    }, 2600)
  })
}

function canAccessPage(page) {
  const rule = pageAccessRules[page]
  if (!rule) return true
  if (rule.loginRequired && currentRole.value === 'guest') return false
  return rule.roles.includes(currentRole.value)
}

function guardPageAccess(page, { notify = true } = {}) {
  if (canAccessPage(page)) return true
  const rule = pageAccessRules[page]
  if (notify && rule) {
    showHeartWall()
  }
  return false
}

function currentHashPath() {
  return window.location.hash.replace(/^#/, '') || '/home'
}

function reloadIntoPage(hashPath, { homeSection } = {}) {
  const normalizedPath = hashPath.startsWith('/') ? hashPath : `/${hashPath}`
  if (homeSection) {
    window.sessionStorage.setItem('pendingHomeSection', homeSection)
  }
  if (currentHashPath() === normalizedPath) return false
  pendingFullPageReload = true
  window.location.hash = normalizedPath
  window.location.reload()
  return true
}

function navigate(page) {
  if (!guardPageAccess(page)) {
    return
  }
  if (reloadIntoPage(`/${page}`)) {
    return
  }
  if (page !== 'alert-detail') {
    currentAlertId.value = null
    selectedAlertDetail.value = null
  }
  currentPage.value = page
  window.location.hash = `/${page}`
  window.scrollTo({ top: 0, behavior: 'smooth' })
  if (page !== 'home') {
    refreshModules()
  }
  if (page === 'profile' || (page === 'appointment' && currentRole.value === 'teacher')) {
    loadUserProfile()
  }
  if (page === 'appointment' && currentRole.value === 'admin') {
    loadStudentList()
  }
  if (page === 'treehole') {
    loadAllTreeholes()
  }
  if (page === 'insights') {
    loadInsights()
  }
  if (page === 'ai-chat' && currentRole.value === 'admin') {
    loadAiChatConfig()
  }
}

async function openArticle(article) {
  if (!guardPageAccess('article')) {
    return
  }
  const articlePath = `/article/${article.id}`
  currentArticleId.value = article.id
  currentPage.value = 'article'
  if (currentRole.value === 'student') {
    try {
      await axios.post(`/api/articles/${article.id}/view-log/`)
    } catch (error) {
      // 资源浏览记录保存失败（静默处理）
    }
  }
  if (reloadIntoPage(articlePath)) {
    return
  }
  window.location.hash = articlePath
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function openTreehole(post) {
  if (!guardPageAccess('treehole')) {
    return
  }
  const treeholePath = `/treehole/${post.id}`
  currentTreeholeId.value = post.id
  currentPage.value = 'treehole-detail'
  if (reloadIntoPage(treeholePath)) {
    return
  }
  window.location.hash = treeholePath
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function loadAllTreeholes() {
  treeholeLoading.value = true
  try {
    const response = await axios.get('/api/treehole-posts/')
    allTreeholes.value = response.data.results ?? response.data
  } catch (error) {
    // 树洞列表加载失败（静默处理）
    allTreeholes.value = []
  } finally {
    treeholeLoading.value = false
  }
}

async function loadTreeholeDetail(treeholeOrId) {
  const treeholeId = typeof treeholeOrId === 'object' ? treeholeOrId.id : treeholeOrId
  if (!treeholeId) return
  try {
    const response = await axios.get(`/api/treehole-posts/${treeholeId}/`)
    const idx = allTreeholes.value.findIndex((t) => String(t.id) === String(treeholeId))
    if (idx >= 0) {
      allTreeholes.value[idx] = response.data
    }
    currentTreeholeId.value = treeholeId
  } catch (error) {
    // 树洞详情加载失败（静默处理）
  }
}

async function submitTreeholeReplyFromDetail() {
  if (!currentTreeholeId.value) return
  const content = replyForms.value[`treehole-${currentTreeholeId.value}`]
  if (!content) return
  await axios.post(`/api/modules/treeholes/${currentTreeholeId.value}/reply/`, {
    content,
    responder_name: currentUser.value?.name || '同伴支持者',
    is_counselor_reply: currentRole.value === 'teacher',
  })
  replyForms.value[`treehole-${currentTreeholeId.value}`] = ''
  moduleMessage.value = '回应已发送。'
  await loadTreeholeDetail(currentTreeholeId.value)
}

async function supportTreehole(postId, event) {
  if (!guardPageAccess('treehole')) return
  try {
    const res = await axios.post(`/api/modules/treeholes/${postId}/support/`)
    // 更新列表中的 support_count
    const post = allTreeholes.value.find((t) => String(t.id) === String(postId))
    if (post) post.support_count = res.data.support_count
    // 更新详情中的 support_count
    if (currentTreehole.value && String(currentTreehole.value.id) === String(postId)) {
      currentTreehole.value.support_count = res.data.support_count
    }
  } catch (error) {
    // 静默处理
  }
}

function scrollToModules() {
  document.querySelector('#modules')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function navigateHomeSection(sectionId = 'home') {
  if (reloadIntoPage('/home', { homeSection: sectionId })) {
    return
  }
  currentPage.value = 'home'
  window.location.hash = '/home'
  await nextTick()
  document.querySelector(`#${sectionId}`)?.scrollIntoView({ behavior: 'smooth', block: sectionId === 'home' ? 'start' : 'center' })
  scheduleScrollMotion()
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
    const [dashboardRes, trendRes, pressureRes, counselorsRes, articlesRes, moduleRes, tagsRes] = await Promise.all([
      axios.get('/api/dashboard/'),
      axios.get('/api/mood-trend/'),
      axios.get('/api/pressure-distribution/'),
      axios.get('/api/recommendations/counselors/'),
      axios.get('/api/articles/'),
      axios.get('/api/modules/'),
      axios.get('/api/tags/'),
    ])

    dashboard.value = dashboardRes.data
    moodTrend.value = trendRes.data
    pressureData.value = pressureRes.data
    counselors.value = counselorsRes.data
    articles.value = articlesRes.data.results ?? articlesRes.data
    tags.value = tagsRes.data.results ?? tagsRes.data
    moduleData.value = moduleRes.data
    syncTeacherProfileForm(moduleRes.data.teacher_counselor)
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
    scheduleScrollMotion()
  } catch (error) {
    loading.value = false
    // API 数据加载失败（静默处理）
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
  syncTeacherProfileForm(moduleRes.data.teacher_counselor)
  if (currentPage.value !== 'alert-detail' && selectedAlertDetail.value && !moduleRes.data.alerts?.some((item) => item.id === selectedAlertDetail.value.alert?.id)) {
    selectedAlertDetail.value = null
  }
  dashboard.value = dashboardRes.data
  moodTrend.value = trendRes.data
  pressureData.value = pressureRes.data
  await nextTick()
  setupChartObservers()
  scheduleRenderCharts()
  scheduleScrollMotion()
}

async function loadCurrentUser() {
  try {
    const response = await axios.get('/api/auth/me/')
    currentUser.value = response.data.authenticated ? response.data.user : null
    syncTeacherProfileForm(currentUser.value?.counselor_profile)
    if (!guardPageAccess(currentPage.value)) {
      navigate('home')
      return
    }
    if (currentPage.value === 'alert-detail' && currentAlertId.value && canViewAlerts.value) {
      await loadAlertStudentDetail(currentAlertId.value)
    }
    if (currentPage.value === 'treehole') {
      await loadAllTreeholes()
    }
    if (currentPage.value === 'treehole-detail' && currentTreeholeId.value) {
      await loadAllTreeholes()
      await loadTreeholeDetail(currentTreeholeId.value)
    }
    if (currentUser.value && currentPage.value === 'profile') {
      await loadUserProfile()
    }
    if (currentPage.value === 'insights') {
      await loadInsights()
    }
    if (currentPage.value === 'ai-chat' && currentRole.value === 'admin') {
      await loadAiChatConfig()
    }
  } catch (error) {
    currentUser.value = null
    // 当前登录状态检查失败（静默处理）
  } finally {
    authReady.value = true
  }
}

function chartReady(el) {
  return el && el.clientWidth > 0 && el.clientHeight > 0
}

function scheduleRenderCharts({ retry = false } = {}) {
  if (!['home', 'insights'].includes(currentPage.value)) return
  if (!retry) chartRenderAttempts = 0
  window.clearTimeout(chartRenderTimer)
  chartRenderTimer = window.setTimeout(async () => {
    await nextTick()
    requestAnimationFrame(() => {
      const rendered = renderCharts()
      resizeCharts()
      if (!rendered && ['home', 'insights'].includes(currentPage.value) && chartRenderAttempts < maxChartRenderAttempts) {
        chartRenderAttempts += 1
        scheduleRenderCharts({ retry: true })
      }
    })
  }, retry ? 80 : 0)
}

function resizeCharts() {
  trendChart?.resize()
  pressureChart?.resize()
  riskChart?.resize()
  appointmentChart?.resize()
}

function setupChartObservers() {
  const targets = [trendChartRef.value, pressureChartRef.value, riskChartRef.value, appointmentChartRef.value].filter(Boolean)
  if (!targets.length) return

  if (!chartResizeObserver) {
    chartResizeObserver = new ResizeObserver(() => {
      scheduleRenderCharts()
    })
  }

  if (!chartVisibilityObserver) {
    chartVisibilityObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // 图表首次进入视口或重新进入 —— 触发动画渲染
            scheduleRenderCharts()
          }
        })
      },
      { threshold: 0.15 },
    )
  }

  targets.forEach((target) => {
    chartResizeObserver.observe(target)
    chartVisibilityObserver.observe(target)
  })
}

function setupScrollReveal() {
  if (scrollRevealObserver) {
    scrollRevealObserver.disconnect()
  }
  scrollRevealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed')
          scrollRevealObserver.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.12, rootMargin: '0px 0px -30px 0px' },
  )
  nextTick(() => {
    document.querySelectorAll('.reveal-on-scroll').forEach((el) => {
      scrollRevealObserver.observe(el)
    })
  })
}

function renderCharts() {
  let renderedTrend = false
  let renderedPressure = false

  // ===== ① 情绪趋势折线图 —— 线从起点描摹到终点 =====
  if (chartReady(trendChartRef.value)) {
    trendChart = trendChart || echarts.init(trendChartRef.value)
    trendChart.setOption({
      animation: true,
      animationDuration: 1000,
      animationEasing: 'cubicInOut',
      tooltip: { trigger: 'axis' },
      legend: { top: 0, data: ['情绪强度', '睡眠质量'] },
      grid: { top: 44, right: 20, bottom: 28, left: 34 },
      xAxis: {
        type: 'category',
        data: moodTrend.value.map((item) => item.date),
        animation: true,
        animationDuration: 600,
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 10,
        animation: true,
        animationDuration: 500,
      },
      series: [
        {
          name: '情绪强度',
          type: 'line',
          smooth: true,
          animation: true,
          animationType: 'line',        // ★ 整条线从左向右描摹
          animationDuration: 1800,
          animationEasing: 'cubicInOut',
          data: moodTrend.value.map((item) => item.intensity),
          lineStyle: { color: '#d85d73', width: 3 },
          itemStyle: { color: '#d85d73' },
          areaStyle: { color: 'rgba(216, 93, 115, 0.12)' },
        },
        {
          name: '睡眠质量',
          type: 'line',
          smooth: true,
          animation: true,
          animationType: 'line',        // ★ 整条线从左向右描摹
          animationDuration: 1800,
          animationDelay: 500,          // 比第一条线晚半秒
          animationEasing: 'cubicInOut',
          data: moodTrend.value.map((item) => item.sleep_quality),
          lineStyle: { color: '#4c8f8a', width: 3 },
          itemStyle: { color: '#4c8f8a' },
        },
      ],
    }, { notMerge: true })
    renderedTrend = true
  }

  // ===== ② 压力来源雷达图 —— 从中心向外扩散 =====
  if (chartReady(pressureChartRef.value)) {
    pressureChart = pressureChart || echarts.init(pressureChartRef.value)
    pressureChart.setOption({
      animation: true,
      animationDuration: 800,
      animationEasing: 'cubicOut',
      tooltip: {},
      radar: {
        indicator: pressureData.value.map((item) => ({ name: item.name, max: 8 })),
        radius: '64%',
        center: ['50%', '52%'],
        animation: true,
        animationDuration: 800,
        axisName: { color: '#555' },
      },
      series: [
        {
          type: 'radar',
          animation: true,
          animationType: 'expansion',   // ★ 由内向外扩散
          animationDuration: 1800,
          animationEasing: 'cubicOut',
          symbol: 'circle',
          symbolSize: 6,
          data: [{
            value: pressureData.value.map((item) => item.value),
            name: '压力来源',
          }],
          areaStyle: { color: 'rgba(240, 173, 99, 0.22)' },
          lineStyle: { color: '#f0ad63', width: 3 },
          itemStyle: { color: '#f0ad63' },
        },
      ],
    }, { notMerge: true })
    renderedPressure = true
  }

  // ===== ③ 风险分布饼图 —— 扇区顺时针依次转出 =====
  if (chartReady(riskChartRef.value)) {
    riskChart = riskChart || echarts.init(riskChartRef.value)
    riskChart.setOption({
      animation: true,
      animationDuration: 1000,
      animationEasing: 'cubicOut',
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          // ★ 扇区沿顺时针依次展开，每个延迟 300ms
          animationType: 'scale',
          animationDuration: 1200,
          animationEasing: 'cubicOut',
          animationDelay: function (idx) { return idx * 300 },
          data: insightData.value?.risk_distribution || [],
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 2,
          },
        },
      ],
    }, { notMerge: true })
  }

  // ===== ④ 预约量表柱状图 —— 柱子从底部逐个升起 =====
  if (chartReady(appointmentChartRef.value)) {
    appointmentChart = appointmentChart || echarts.init(appointmentChartRef.value)
    appointmentChart.setOption({
      animation: true,
      animationDuration: 800,
      animationEasing: 'cubicOut',
      tooltip: { trigger: 'axis' },
      grid: { top: 18, right: 20, bottom: 32, left: 42 },
      xAxis: {
        type: 'category',
        data: (insightData.value?.appointment_distribution || []).map((item) => item.name),
        animation: true,
        animationDuration: 500,
      },
      yAxis: {
        type: 'value',
        animation: true,
        animationDuration: 400,
      },
      series: [
        {
          type: 'bar',
          animation: true,
          animationType: 'scale',       // ★ 从底部升起
          animationDuration: 1400,
          animationEasing: 'cubicOut',
          animationDelay: function (idx) { return idx * 220 },
          data: (insightData.value?.appointment_distribution || []).map((item) => item.value),
          itemStyle: {
            color: '#4c8f8a',
            borderRadius: [6, 6, 0, 0],
          },
        },
      ],
    }, { notMerge: true })
  }

  return renderedTrend && renderedPressure
}

watch([currentPage, moodTrend, pressureData, insightData, currentUser, loading], async () => {
  if (loading.value) return
  await nextTick()
  setupScrollReveal()
  if (['home', 'insights'].includes(currentPage.value)) {
    setupChartObservers()
    // 仅当图表容器确实在视口内才立即渲染，其余由 IntersectionObserver 触发
    nextTick(() => {
      const inView = (el) => {
        if (!el) return false
        const rect = el.getBoundingClientRect()
        return rect.top < window.innerHeight && rect.bottom > 0
      }
      if (inView(trendChartRef.value) || inView(pressureChartRef.value) ||
          inView(riskChartRef.value) || inView(appointmentChartRef.value)) {
        scheduleRenderCharts()
      }
    })
  }
}, { flush: 'post' })

watch(() => tagPopup.value.visible, (visible) => {
  if (visible) {
    const handler = (e) => {
      if (!e.target.closest('.tag-popup-panel') && !e.target.closest('.tag-add-button')) {
        closeTagPopup()
      }
    }
    window.setTimeout(() => document.addEventListener('click', handler), 0)
    tagPopup._clickHandler = handler
  } else {
    if (tagPopup._clickHandler) {
      document.removeEventListener('click', tagPopup._clickHandler)
      tagPopup._clickHandler = null
    }
  }
})

onMounted(() => {
  handleScroll()
  setupAiSpeechRecognition()
  setupScrollReveal()
  loadBackendData()
  loadCurrentUser()
  window.addEventListener('pointermove', handlePointerMove)
  window.addEventListener('scroll', handleScroll, { passive: true })
  window.addEventListener('resize', scheduleRenderCharts)
  window.addEventListener('hashchange', () => {
    if (pendingFullPageReload) return
    const parts = window.location.hash?.replace('#/', '').split('/') || ['home']
    const nextPage = parts[0] || 'home'
    if (!guardPageAccess(nextPage)) {
      navigate('home')
      return
    }
    window.location.reload()
  })
  nextTick(() => {
    scheduleScrollMotion()
    const pendingHomeSection = window.sessionStorage.getItem('pendingHomeSection')
    if (currentPage.value === 'home' && pendingHomeSection) {
      window.sessionStorage.removeItem('pendingHomeSection')
      document.querySelector(`#${pendingHomeSection}`)?.scrollIntoView({
        behavior: 'smooth',
        block: pendingHomeSection === 'home' ? 'start' : 'center',
      })
    }
  })
})

watch(resourceSearch, () => {
  resourcePage.value = 1
})

watch(counselorSearch, () => {
  counselorPage.value = 1
})

onUnmounted(() => {
  stopAiSpeechInput()
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', scheduleRenderCharts)
  window.clearTimeout(chartRenderTimer)
  window.clearTimeout(heartWallTimer)
  window.cancelAnimationFrame(scrollMotionFrame)
  chartResizeObserver?.disconnect()
  chartVisibilityObserver?.disconnect()
  scrollRevealObserver?.disconnect()
  trendChart?.dispose()
  pressureChart?.dispose()
})

const features = [
  {
    page: 'mood',
    title: '情绪打卡',
    subtitle: '记录每天的心情变化',
    desc: '用表情、强度和影响因素记录每天的状态，形成连续的情绪轨迹。',
    stat: '7 日趋势',
    accent: 'rose',
    detail: '支持心情标签、压力来源、睡眠状态和简短日记，自动生成近一周趋势，让学生更早看见自己的变化。',
  },
  {
    page: 'treehole',
    title: '匿名树洞',
    subtitle: '把难说出口的烦恼放下来',
    desc: '把难以开口的困扰安全表达出来，获得同伴温和回应与支持。',
    stat: '匿名表达',
    accent: 'pink',
    detail: '发布内容默认匿名，结合关键词提醒与温和引导，帮助学生在被理解的氛围里表达压力、关系和成长困惑。',
  },
  {
    page: 'ai-chat',
    title: 'AI 倾听',
    subtitle: '把此刻的压力慢慢说清',
    desc: '登录后可进入对话，把压力、情绪或困扰写下来，获得即时倾听与情绪梳理。',
    stat: '即时陪伴',
    accent: 'rose',
    detail: '接入 AI 倾听助手，提供温和回应、情绪梳理和短时可执行建议，同时保留真人支持提醒。',
  },
  {
    page: 'assessment',
    title: '心理测评',
    subtitle: '自助了解压力与风险信号',
    desc: '提供压力、睡眠、情绪等自评问卷，结果只作风险提示与资源推荐。',
    stat: '自助筛查',
    accent: 'amber',
    detail: '测评结果以非诊断方式呈现，提供分层建议、资源链接和后续跟进入口，避免给学生制造额外负担。',
  },
  {
    page: 'appointment',
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

const aiListeningFeatures = [
  {
    title: '温和对话陪伴',
    text: '梳理压力与情绪。',
  },
  {
    title: '语音转文字输入',
    text: '把语音转成文字。',
  },
  {
    title: '风险表达提醒',
    text: '识别高风险表达。',
  },
  {
    title: '短时调节建议',
    text: '给出可执行建议。',
  },
]

function charLength(value) {
  return Array.from(String(value || '').trim()).length
}

function isValidEmail(value) {
  if (!value) return true
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value).trim())
}

function isValidPassword(value) {
  return /^(?=.*[a-z])(?=.*[A-Z]).{8,}$/.test(String(value || ''))
}

function hasValidPressureSources(items) {
  return items.every((item) => charLength(item) <= 20)
}

function validateCommonFields({ username, name, email, password, studentNo, grade, pressureSources } = {}) {
  if (username !== undefined && charLength(username) > 20) return '账号不能超过20个字符。'
  if (name !== undefined && charLength(name) > 12) return '姓名不能超过12个字符。'
  if (email !== undefined && !isValidEmail(email)) return '邮箱格式不正确。'
  if (password !== undefined && !isValidPassword(password)) return '密码至少8位，且必须同时包含大写字母和小写字母。'
  if (studentNo !== undefined && charLength(studentNo) > 50) return '学号不能超过50个字符。'
  if (grade !== undefined && grade && !/^\d{4}$/.test(String(grade).trim())) return '年级只能输入四位数字。'
  if (pressureSources !== undefined && !hasValidPressureSources(pressureSources)) return '压力来源每项不能超过20个字。'
  return ''
}

function formatDateTimeInput(date) {
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function validateAppointmentTime(value) {
  if (!value) return '请选择预约时间。'
  const selected = new Date(value)
  if (Number.isNaN(selected.getTime())) return '预约时间格式不正确。'
  if (selected.getTime() <= Date.now()) return '预约时间不能早于当前时间。'
  return ''
}

function confirmAppointmentTime() {
  appointmentTimeInput.value?.blur()
}

function setAuthRole(role) {
  authForm.value.role = roleFormValues[role] || '学生'
  authMessage.value = ''
}

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
      role: authForm.value.role,
    }
    const response = await axios.post('/api/auth/login/', payload)
    currentUser.value = response.data.user
    authMessage.value = response.data.detail || '操作成功'
    showAuth.value = false
    window.location.reload()
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
    const pressureSources = pressureSourceList(authForm.value.pressureSources)
    const validationError = validateCommonFields({
      username: authForm.value.username,
      name: authForm.value.name,
      email: authForm.value.email,
      password: authForm.value.password,
      studentNo: authForm.value.role === '学生' ? authForm.value.studentNo : undefined,
      grade: authForm.value.role === '学生' ? authForm.value.grade : undefined,
      pressureSources: authForm.value.role === '学生' ? pressureSources : undefined,
    })
    if (validationError) {
      authMessage.value = validationError
      return
    }
    if (activeAuthRole.value !== 'student' && !authForm.value.invitationCode.trim()) {
      authMessage.value = `注册${activeAuthRoleLabel.value}账号需要填写对应的邀请码。`
      return
    }
    const payload = {
      username: authForm.value.username,
      password: authForm.value.password,
      confirm_password: authForm.value.confirmPassword,
      role: authForm.value.role,
      invitation_code: authForm.value.invitationCode,
      name: authForm.value.name,
      email: authForm.value.email,
      student_no: authForm.value.studentNo,
      college: authForm.value.college,
      grade: authForm.value.grade,
      pressure_sources: pressureSources,
      preferred_topics: pressureSourceList(authForm.value.preferredTopics),
      privacy_consent: authForm.value.privacyConsent,
      teacher_title: authForm.value.teacherTitle,
      teacher_specialties: pressureSourceList(authForm.value.teacherSpecialties),
      teacher_qualifications: authForm.value.teacherQualifications,
    }
    const response = await axios.post('/api/auth/register/', payload)
    currentUser.value = response.data.user
    authMessage.value = response.data.detail || '注册成功'
    window.location.hash = '#/details'
    window.location.reload()
  } catch (error) {
    authMessage.value = error.response?.data?.detail || '注册失败，请检查输入后重试。'
  } finally {
    authSubmitting.value = false
  }
}

async function logoutAccount() {
  await axios.post('/api/auth/logout/')
  currentUser.value = null
  if (!canAccessPage(currentPage.value)) {
    showHeartWall()
    navigate('home')
  }
}

function pressureSourceList(value) {
  return String(value || '')
    .split(/[，,、\s]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function syncInvitationCodes(codes = []) {
  const nextDrafts = { teacher: '', admin: '' }
  const nextLocks = { teacher: false, admin: false }
  codes.forEach((item) => {
    if (!item?.target_role) return
    nextDrafts[item.target_role] = item.code || ''
    nextLocks[item.target_role] = Boolean(item.is_locked)
  })
  invitationDrafts.value = nextDrafts
  invitationLocks.value = nextLocks
}

function randomInvitationCode() {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!"#$%&\\\'()*+,-./:;<=>?@[\\\\]^_`{|}~'
  const values = window.crypto?.getRandomValues
    ? window.crypto.getRandomValues(new Uint8Array(16))
    : Array.from({ length: 16 }, () => Math.floor(Math.random() * alphabet.length))
  return Array.from(values, (value) => alphabet[value % alphabet.length]).join('')
}

function generateInvitation(role) {
  if (invitationLocks.value[role]) return
  invitationDrafts.value[role] = randomInvitationCode()
  invitationLocks.value[role] = false
}

function showInvitationCopyToast(event) {
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0
  const x = Math.min(Math.max(event?.clientX ?? viewportWidth / 2, 28), Math.max(28, viewportWidth - 28))
  const y = Math.min(Math.max((event?.clientY ?? viewportHeight / 2) - 10, 24), Math.max(24, viewportHeight - 24))
  invitationCopyToast.value = {
    visible: true,
    x,
    y,
  }
  window.clearTimeout(invitationCopyToastTimer)
  invitationCopyToastTimer = window.setTimeout(() => {
    invitationCopyToast.value.visible = false
  }, 1200)
}

async function copyInvitation(role, event) {
  const code = invitationDrafts.value[role]
  if (!code) return
  try {
    await navigator.clipboard.writeText(code)
  } catch (error) {
    const textarea = document.createElement('textarea')
    textarea.value = code
    textarea.setAttribute('readonly', '')
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
  showInvitationCopyToast(event)
}

async function copyLockedInvitation(role, event) {
  if (!invitationLocks.value[role]) return
  await copyInvitation(role, event)
}

async function lockInvitation(role, event) {
  if (invitationLocks.value[role]) {
    try {
      const response = await axios.post('/api/auth/invitations/', {
        target_role: role,
        is_locked: false,
      })
      syncInvitationCodes(response.data.invitation_codes)
    } catch (error) {
      // 邀请码解锁失败（静默处理）
    }
    return
  }
  const code = String(invitationDrafts.value[role] || '').trim()
  if (!code) {
    return
  }
  try {
    const response = await axios.post('/api/auth/invitations/', {
      target_role: role,
      code,
    })
    syncInvitationCodes(response.data.invitation_codes)
    await copyInvitation(role, event)
  } catch (error) {
    // 邀请码保存失败（静默处理）
  }
}

function syncTeacherProfileForm(profile) {
  if (!profile) return
  teacherProfileForm.value = {
    name: profile.name || currentUser.value?.name || '',
    title: profile.title || '心理教师',
    specialties: (profile.specialties || []).join('，'),
    qualifications: profile.qualifications || '',
    available_slots: (profile.available_slots || []).join('，'),
  }
}

function syncProfileForm(payload) {
  if (!payload?.user) return
  const student = payload.student || {}
  const teacher = payload.teacher_counselor || payload.user.counselor_profile || {}
  profileForm.value = {
    name: payload.user.name || '',
    email: payload.user.email || '',
    college: student.college || '',
    grade: student.grade || '',
    pressure_sources: (student.pressure_sources || []).join('，'),
    preferred_topics: (student.preferred_topics || []).join('，'),
    privacy_consent: Boolean(student.privacy_consent),
    title: teacher.title || '心理教师',
    specialties: (teacher.specialties || []).join('，'),
    qualifications: teacher.qualifications || '',
    available_slots: (teacher.available_slots || []).join('，'),
  }
  syncInvitationCodes(payload.invitation_codes || [])
}

async function loadUserProfile() {
  if (!currentUser.value) return
  const response = await axios.get('/api/auth/profile/')
  syncProfileForm(response.data)
}

async function submitUserProfile() {
  profileMessage.value = ''
  const pressureSources = pressureSourceList(profileForm.value.pressure_sources)
  const validationError = validateCommonFields({
    name: profileForm.value.name,
    email: profileForm.value.email,
    grade: currentRole.value === 'student' ? profileForm.value.grade : undefined,
    pressureSources: currentRole.value === 'student' ? pressureSources : undefined,
  })
  if (validationError) {
    profileMessage.value = validationError
    return
  }
  try {
    const response = await axios.patch('/api/auth/profile/', {
      name: profileForm.value.name,
      email: profileForm.value.email,
      college: profileForm.value.college,
      grade: profileForm.value.grade,
      pressure_sources: pressureSources,
      preferred_topics: pressureSourceList(profileForm.value.preferred_topics),
      privacy_consent: profileForm.value.privacy_consent,
      title: profileForm.value.title,
      specialties: pressureSourceList(profileForm.value.specialties),
      qualifications: profileForm.value.qualifications,
      available_slots: pressureSourceList(profileForm.value.available_slots),
    })
    currentUser.value = response.data.user
    syncProfileForm(response.data)
    syncTeacherProfileForm(response.data.teacher_counselor)
    profileMessage.value = '个人资料已保存。'
    await refreshModules()
  } catch (error) {
    profileMessage.value = error.response?.data?.detail || '资料保存失败，请检查输入后重试。'
  }
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
  const validationError = validateCommonFields({ pressureSources: payload.pressure_sources })
  if (validationError) {
    moduleMessage.value = validationError
    return
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
  const validationError = validateAppointmentTime(appointmentForm.value.scheduled_at)
  if (validationError) {
    moduleMessage.value = validationError
    return
  }
  try {
    await axios.post('/api/modules/appointments/', appointmentForm.value)
    appointmentForm.value.topic = ''
    appointmentForm.value.confidential_note = ''
    moduleMessage.value = '预约已提交，等待心理老师确认。'
    await refreshModules()
  } catch (error) {
    moduleMessage.value = error.response?.data?.detail || '预约提交失败，请检查时间和内容后重试。'
  }
}

async function loadStudentList() {
  if (!canManage.value) return
  try {
    const response = await axios.get('/api/students/')
    studentList.value = response.data.results ?? response.data
  } catch (error) {
    // 学生列表加载失败（静默处理）
  }
}

async function createCounselorFromStudent() {
  if (!canManage.value || !counselorCreateForm.value.student_id) {
    counselorCreateMessage.value = '请先选择学生。'
    return
  }
  counselorCreateLoading.value = true
  counselorCreateMessage.value = ''
  const form = counselorCreateForm.value
  const validationError = validateCommonFields({ name: form.name })
  if (validationError) {
    counselorCreateMessage.value = validationError
    counselorCreateLoading.value = false
    return
  }
  try {
    const response = await axios.post('/api/counselors/', {
      user: form.student_id,
      name: form.name,
      title: form.title,
      specialties: pressureSourceList(form.specialties),
      qualifications: form.qualifications,
      available_slots: pressureSourceList(form.available_slots),
      avatar_color: form.avatar_color,
      is_active: true,
      source: '管理员指派',
    })
    counselorCreateMessage.value = `已成功将 ${response.data.name} 添加为咨询师。`
    counselorCreateForm.value = {
      student_id: null,
      name: '',
      title: '心理教师',
      specialties: '',
      qualifications: '',
      available_slots: '',
      avatar_color: '#d85d73',
    }
    await Promise.all([
      refreshModules(),
      loadStudentList(),
    ])
  } catch (error) {
    counselorCreateMessage.value = error.response?.data?.detail || '创建咨询师失败，请重试。'
  } finally {
    counselorCreateLoading.value = false
  }
}

function scrollAiChatToBottom() {
  nextTick(() => {
    if (aiChatWindowRef.value) {
      aiChatWindowRef.value.scrollTop = aiChatWindowRef.value.scrollHeight
    }
  })
}

function appendAiSpeechText(text) {
  const value = String(text || '').trim()
  if (!value) return
  aiChatInput.value = `${aiChatInput.value}${aiChatInput.value.trim() ? '\n' : ''}${value}`
}

function clearAiSpeechSilenceTimer() {
  window.clearTimeout(aiSpeechSilenceTimer)
  aiSpeechSilenceTimer = null
}

function startAiSpeechSilenceTimer() {
  clearAiSpeechSilenceTimer()
  aiSpeechSilenceTimer = window.setTimeout(() => {
    if (aiSpeechListening.value && aiSpeechRecognition) {
      aiSpeechMessage.value = '5 秒内未检测到声音，已自动停止。'
      aiSpeechRecognition.stop()
    }
  }, 5000)
}

function setupAiSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  aiSpeechSupported.value = Boolean(SpeechRecognition)
  if (!SpeechRecognition) {
    aiSpeechMessage.value = '当前浏览器不支持语音转文字。'
    return
  }

  aiSpeechRecognition = new SpeechRecognition()
  aiSpeechRecognition.lang = 'zh-CN'
  aiSpeechRecognition.continuous = false
  aiSpeechRecognition.interimResults = true

  aiSpeechRecognition.onstart = () => {
    aiSpeechListening.value = true
    aiSpeechMessage.value = '正在聆听，5 秒内没有声音将自动停止...'
    startAiSpeechSilenceTimer()
  }
  aiSpeechRecognition.onend = () => {
    aiSpeechListening.value = false
    clearAiSpeechSilenceTimer()
    if (aiSpeechMessage.value === '正在聆听，5 秒内没有声音将自动停止...') {
      aiSpeechMessage.value = ''
    }
  }
  aiSpeechRecognition.onsoundstart = clearAiSpeechSilenceTimer
  aiSpeechRecognition.onspeechstart = clearAiSpeechSilenceTimer
  aiSpeechRecognition.onerror = (event) => {
    aiSpeechListening.value = false
    clearAiSpeechSilenceTimer()
    aiSpeechMessage.value = event.error === 'not-allowed' ? '浏览器未允许麦克风权限。' : '语音识别暂时不可用。'
  }
  aiSpeechRecognition.onresult = (event) => {
    clearAiSpeechSilenceTimer()
    let finalText = ''
    let interimText = ''
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const text = event.results[index][0]?.transcript || ''
      if (event.results[index].isFinal) {
        finalText += text
      } else {
        interimText += text
      }
    }
    if (finalText.trim()) {
      appendAiSpeechText(finalText)
      aiSpeechMessage.value = '已转写到输入框。'
    } else if (interimText.trim()) {
      aiSpeechMessage.value = `识别中：${interimText.trim()}`
    }
  }
}

function toggleAiSpeechInput() {
  if (!aiSpeechSupported.value || !aiSpeechRecognition) {
    aiSpeechMessage.value = '当前浏览器不支持语音转文字。'
    return
  }
  if (aiSpeechListening.value) {
    aiSpeechRecognition.stop()
    return
  }
  try {
    aiSpeechRecognition.start()
  } catch (error) {
    aiSpeechMessage.value = '语音识别启动失败，请稍后再试。'
  }
}

function stopAiSpeechInput() {
  clearAiSpeechSilenceTimer()
  if (aiSpeechRecognition && aiSpeechListening.value) {
    aiSpeechRecognition.stop()
  }
}

function syncAiConfigForm(data) {
  const nextUrl = data.api_url || 'https://api.openai.com/v1/chat/completions'
  const nextProvider = data.provider || (nextUrl.includes('api.deepseek.com') ? 'deepseek' : 'openai')
  aiConfigForm.value.enabled = data.enabled ?? true
  aiConfigForm.value.api_key = ''
  aiConfigForm.value.api_key_masked = data.api_key_masked || ''
  aiConfigForm.value.api_url = nextUrl
  aiConfigForm.value.model = data.model || 'gpt-4o-mini'
  aiConfigForm.value.auto_detect_model = Boolean(data.auto_detect_model)
  aiConfigForm.value.timeout = data.timeout || 30
  aiConfigForm.value.configured = Boolean(data.configured)
  aiConfigForm.value.source = data.source || ''
  aiConfigForm.value.provider = nextProvider
}

function selectAiProvider(providerId) {
  const preset = aiProviderPresets.find((item) => item.id === providerId)
  if (!preset) return
  aiConfigForm.value.provider = preset.id
  aiConfigForm.value.api_url = preset.api_url
  aiConfigForm.value.model = preset.model
}

async function loadAiChatConfig() {
  if (currentRole.value !== 'admin') return
  aiConfigLoading.value = true
  aiConfigMessage.value = ''
  try {
    const response = await axios.get('/api/ai-chat/config/')
    syncAiConfigForm(response.data)
  } catch (error) {
    aiConfigMessage.value = error.response?.data?.detail || 'AI 配置加载失败。'
  } finally {
    aiConfigLoading.value = false
  }
}

async function saveAiChatConfig() {
  if (currentRole.value !== 'admin') return
  aiConfigSaving.value = true
  aiConfigMessage.value = ''
  try {
    const response = await axios.patch('/api/ai-chat/config/', {
      enabled: aiConfigForm.value.enabled,
      provider: aiConfigForm.value.provider,
      api_key: aiConfigForm.value.api_key,
      api_url: aiConfigForm.value.api_url,
      model: aiConfigForm.value.model,
      auto_detect_model: aiConfigForm.value.auto_detect_model,
      timeout: aiConfigForm.value.timeout,
    })
    syncAiConfigForm(response.data)
    aiConfigMessage.value = response.data.detail || 'AI 对话配置已保存。'
  } catch (error) {
    aiConfigMessage.value = error.response?.data?.detail || 'AI 配置保存失败，请检查地址、模型和 Key。'
  } finally {
    aiConfigSaving.value = false
  }
}

async function sendAiChatMessage() {
  const content = aiChatInput.value.trim()
  if (!content || aiChatSending.value) return
  if (!canUseAiChat.value) {
    aiChatMessage.value = '请登录后再进入 AI 倾听对话。'
    return
  }

  aiChatMessage.value = ''
  aiChatInput.value = ''
  aiChatMessages.value.push({ role: 'user', content })
  aiChatSending.value = true
  scrollAiChatToBottom()

  try {
    const payloadMessages = aiChatMessages.value
      .slice(-12)
      .map((item) => ({ role: item.role, content: item.content }))
    const response = await axios.post('/api/ai-chat/', { messages: payloadMessages })
    aiChatMessages.value.push({ role: 'assistant', content: response.data.reply })
    if (response.data.risk_detected) {
      aiChatMessage.value = '平台已识别到高风险表达，建议同时联系学校心理中心、辅导员或身边可信任的人。'
    }
  } catch (error) {
    aiChatMessages.value.push({
      role: 'assistant',
      content: error.response?.data?.detail || 'AI 倾听服务暂时不可用，请稍后再试。',
    })
  } finally {
    aiChatSending.value = false
    scrollAiChatToBottom()
  }
}

function clearAiChat() {
  aiChatInput.value = ''
  aiChatMessage.value = ''
  stopAiSpeechInput()
  aiChatMessages.value = [
    {
      role: 'assistant',
      content: '新的对话已经开始。你可以继续说说现在最困扰你的事情。',
    },
  ]
  scrollAiChatToBottom()
}

async function submitTeacherProfile() {
  if (currentRole.value !== 'teacher') return
  const validationError = validateCommonFields({ name: teacherProfileForm.value.name })
  if (validationError) {
    moduleMessage.value = validationError
    return
  }
  const response = await axios.patch('/api/auth/teacher-profile/', {
    name: teacherProfileForm.value.name,
    title: teacherProfileForm.value.title,
    specialties: pressureSourceList(teacherProfileForm.value.specialties),
    qualifications: teacherProfileForm.value.qualifications,
    available_slots: pressureSourceList(teacherProfileForm.value.available_slots),
  })
  syncTeacherProfileForm(response.data)
  moduleMessage.value = '教师个人资料已保存，学生预约列表会同步更新。'
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

function alertLevelLabel(level) {
  const labels = {
    notice: '关注',
    warning: '预警',
    critical: '危机',
  }
  return labels[level] || level || '未知等级'
}

function riskLevelLabel(level) {
  const labels = {
    low: '低',
    medium: '中',
    high: '高',
  }
  return labels[level] || level || '未知风险'
}

function treeholeCategoryLabel(category) {
  const labels = {
    study: '学业压力',
    relationship: '人际关系',
    family: '家庭关系',
    growth: '自我成长',
    other: '其他',
  }
  return labels[category] || category || '其他'
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

function changeMoodPage(page) {
  moodPage.value = Math.min(Math.max(1, page), moodTotalPages.value)
}

function changeTreeholePage(page) {
  treeholePage.value = Math.min(Math.max(1, page), treeholeTotalPages.value)
}

function changeRecordPage(page) {
  recordPage.value = Math.min(Math.max(1, page), recordTotalPages.value)
}

function changeAlertPage(page) {
  alertPage.value = Math.min(Math.max(1, page), alertTotalPages.value)
}

function formatList(value) {
  if (Array.isArray(value)) return value.length ? value.join('、') : '暂无'
  return value || '暂无'
}

async function loadInsights() {
  insightLoading.value = true
  insightMessage.value = ''
  try {
    const response = await axios.get('/api/insights/')
    insightData.value = response.data
    insightLoading.value = false
    await nextTick()
    setupChartObservers()
    scheduleRenderCharts()
  } catch (error) {
    insightLoading.value = false
    insightMessage.value = error.response?.data?.detail || '数据洞察加载失败，请确认后端服务已启动。'
  }
}

async function downloadInsightExport(format) {
  if (!canDownloadInsights.value) {
    return
  }
  const extension = format === 'excel' ? 'xlsx' : 'csv'
  try {
    let response
    try {
      response = await axios.get(`/api/export-insights/${format}/`, {
        responseType: 'blob',
        withCredentials: true,
      })
    } catch (error) {
      if (error.response?.status !== 404) throw error
      response = await axios.get(`/api/export-insights/${format}`, {
        responseType: 'blob',
        withCredentials: true,
      })
    }
    const contentType = response.headers['content-type'] || 'application/octet-stream'
    if (contentType.includes('application/json')) {
      const errorText = await response.data.text()
      const errorData = JSON.parse(errorText)
      insightMessage.value = errorData.detail || '导出失败，请确认当前账号是否为教师或管理员。'
      return
    }

    const blob = new Blob([response.data], { type: contentType })
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `数据洞察-${new Date().toISOString().slice(0, 10)}.${extension}`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(blobUrl)
  } catch (error) {
    if (error.response?.data instanceof Blob) {
      const errorText = await error.response.data.text()
      try {
        const errorData = JSON.parse(errorText)
        insightMessage.value = errorData.detail || '导出失败，请稍后重试。'
      } catch {
        insightMessage.value = errorText || '导出失败，请稍后重试。'
      }
      return
    }
    insightMessage.value = `导出失败（${error.response?.status || '网络错误'}），请确认后端已重启。`
  }
}

function downloadChart(chart, filename) {
  if (!canDownloadInsights.value) {
    return
  }
  if (!chart) {
    return
  }
  const link = document.createElement('a')
  link.href = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' })
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
}

function downloadInsightCharts() {
  downloadChart(trendChart, '情绪与睡眠趋势.png')
  downloadChart(pressureChart, '压力来源雷达图.png')
  downloadChart(riskChart, '风险等级分布.png')
  downloadChart(appointmentChart, '预约状态分布.png')
}

function openAlertStudentDetail(alert) {
  if (!guardPageAccess('alert-detail')) {
    return
  }
  const alertPath = `/alert-detail/${alert.id}`
  currentAlertId.value = alert.id
  currentPage.value = 'alert-detail'
  if (reloadIntoPage(alertPath)) {
    return
  }
  window.location.hash = alertPath
  window.scrollTo({ top: 0, behavior: 'smooth' })
  loadAlertStudentDetail(alert.id)
}

async function loadAlertStudentDetail(alertOrId) {
  if (!canViewAlerts.value) return
  const alertId = typeof alertOrId === 'object' ? alertOrId.id : alertOrId
  if (!alertId) return
  currentAlertId.value = alertId
  alertDetailLoading.value = true
  alertDetailMessage.value = ''
  try {
    const response = await axios.get(`/api/alerts/${alertId}/student-detail/`)
    selectedAlertDetail.value = response.data
  } catch (error) {
    alertDetailMessage.value = error.response?.data?.detail || '预警学生详情加载失败'
  } finally {
    alertDetailLoading.value = false
  }
}

async function editAlert(alert) {
  if (!canManage.value) return
  await adminPatch(`/api/crisis-alerts/${alert.id}/`, { handled: !alert.handled })
  if (selectedAlertDetail.value?.alert?.id === alert.id) {
    await loadAlertStudentDetail(alert.id)
  }
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
    <Transition name="heart-wall">
      <div v-if="heartWallVisible" :key="heartWallKey" class="heart-wall-toast" role="status" aria-live="polite">
        <strong>心之壁</strong>
      </div>
    </Transition>
    <Transition name="copy-toast">
      <div
        v-if="invitationCopyToast.visible"
        class="invitation-copy-toast"
        :style="{ left: `${invitationCopyToast.x}px`, top: `${invitationCopyToast.y}px` }"
        role="status"
        aria-live="polite"
      >
        已复制
      </div>
    </Transition>
    <Transition name="tag-popup">
      <div
        v-if="tagPopup.visible"
        class="tag-popup-panel"
        :style="{ left: `${tagPopup.x}px`, top: `${tagPopup.y}px` }"
        @click.stop
      >
        <div class="tag-popup-head">
          <span>添加标签</span>
          <button class="tag-popup-close" type="button" @click="closeTagPopup">&times;</button>
        </div>
        <div class="tag-popup-existing">
          <button
            v-for="tag in popupVisibleTags"
            :key="tag.id || tag.name"
            class="tag-popup-chip"
            type="button"
            @click="selectExistingTag(tag.name)"
          >{{ tag.name }}</button>
          <button
            v-if="popupHasMoreTags"
            class="tag-popup-chip more-chip"
            type="button"
            @click="tagPopup.showAll = true"
          >...</button>
          <span v-if="popupAvailableTags.length === 0" class="tag-popup-empty">暂无可选标签</span>
        </div>
        <form class="tag-popup-new" @submit.prevent="submitPopupNewTag">
          <input
            v-model.trim="tagPopup.newTag"
            maxlength="30"
            placeholder="输入新标签名"
          />
          <button type="submit" :disabled="!tagPopup.newTag.trim()">添加</button>
        </form>
      </div>
    </Transition>
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
        <a
          href="#/ai-chat"
          :aria-disabled="!authReady"
          @click.prevent="authReady && navigate('ai-chat')"
        >AI 倾听</a>
        <a href="#/assessment" @click.prevent="navigate('assessment')">心理测评</a>
        <a href="#/appointment" @click.prevent="navigate('appointment')">咨询预约</a>
        <a href="#/insights" @click.prevent="navigate('insights')">数据洞察</a>
        <a href="#/resources" @click.prevent="navigate('resources')">心理资源</a>
        <a
          v-if="!authReady || canViewAlerts"
          :class="['alert-nav-link', { 'nav-placeholder': !authReady || !canViewAlerts }]"
          :aria-hidden="!authReady || !canViewAlerts"
          :tabindex="!authReady || !canViewAlerts ? -1 : 0"
          href="#/alerts"
          @click.prevent="authReady && canViewAlerts && navigate('alerts')"
        >预警管理</a>
      </nav>

      <div :class="['auth-actions', { ready: authReady }]">
        <div v-if="!authReady" class="auth-actions-placeholder" aria-hidden="true"></div>
        <template v-else-if="currentUser">
          <div class="user-menu">
            <button class="user-chip" type="button" @click="navigate('profile')">{{ currentUser.name }}</button>
            <div class="user-dropdown">
              <button type="button" @click="navigate('profile')">个人资料</button>
              <button type="button" @click="logoutAccount">退出登录</button>
            </div>
          </div>
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
        <div class="section-heading align-left wide-heading reveal-on-scroll">
          <span class="eyebrow">核心功能</span>
          <h2>从日常表达，到专业支持</h2>
          <p>平台不是单一的论坛或预约系统，而是一套围绕学生心理状态变化展开的支持路径。</p>
        </div>

        <div class="feature-grid">
          <article
            v-for="(feature, index) in features"
            :key="feature.title"
            :class="['feature-card', 'scroll-converge', 'reveal-on-scroll', feature.accent]"
            v-bind="motionAttrs(index, features.length, 120)"
            tabindex="0"
            @click="navigate(feature.page)"
            @keydown.enter="navigate(feature.page)"
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
          <article v-for="(scene, index) in scenes" :key="scene.label" class="scene-item scroll-converge" v-bind="motionAttrs(index, scenes.length, 92)">
            <span>{{ scene.label }}</span>
            <div>
              <h3>{{ scene.title }}</h3>
              <p>{{ scene.text }}</p>
            </div>
          </article>
        </div>
      </section>

      <section id="process" class="section process-section scroll-follow follow-medium">
        <div class="section-heading align-left wide-heading reveal-on-scroll">
          <span class="eyebrow">支持流程</span>
          <h2>清晰的心理支持闭环</h2>
        </div>
        <div class="process-line">
          <div v-for="(step, index) in steps" :key="step" class="process-step scroll-converge" v-bind="motionAttrs(index, steps.length, 110)">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <p>{{ step }}</p>
          </div>
        </div>
      </section>

      <section id="ai-listening" class="section ai-showcase-section scroll-follow follow-medium">
        <div class="section-heading align-left wide-heading reveal-on-scroll">
          <span class="eyebrow">AI 倾听</span>
          <h2>在正式求助前，先把感受说出来</h2>
          <p>AI 倾听面向学生和心理老师开放，提供低压力的即时对话入口。游客可在首页了解功能，进入对话前需要登录。</p>
        </div>

        <div class="ai-showcase-panel scroll-converge" v-bind="motionAttrs(0, 1, 108)">
          <div class="ai-showcase-bg" aria-hidden="true">
            <article v-for="(item, index) in aiListeningFeatures" :key="item.title">
              <span>{{ String(index + 1).padStart(2, '0') }}</span>
              <strong>{{ item.title }}</strong>
              <p>{{ item.text }}</p>
            </article>
          </div>

          <div class="ai-showcase-chat-preview" aria-label="AI 倾听聊天展示">
            <div class="ai-showcase-chat-head">
              <span>当前对话</span>
              <strong>浏览展示</strong>
            </div>
            <div class="ai-showcase-bubble assistant">
              <span>AI</span>
              <p>你好，我是平台里的 AI 倾听助手。你可以把此刻的压力、情绪或困扰告诉我，我们先一起把它慢慢理清。</p>
            </div>
            <div class="ai-showcase-bubble user">
              <span>我</span>
              <p>最近压力很大，晚上总是睡不着。</p>
            </div>
            <div class="ai-showcase-bubble assistant">
              <span>AI</span>
              <p>我们先把压力来源分开看。你可以先写下最影响睡眠的一件事，再试一次 3 分钟呼吸放松。</p>
            </div>
            <div class="ai-showcase-divider" aria-hidden="true"><span></span><strong></strong><span></span></div>
            <div class="ai-showcase-input-preview" aria-hidden="true">
              <div class="ai-showcase-textarea">写下你现在的感受、压力来源或想聊的事情</div>
              <svg class="ai-showcase-mic" viewBox="0 0 24 24" focusable="false">
                <path d="M12 14.5a4 4 0 0 0 4-4V6a4 4 0 0 0-8 0v4.5a4 4 0 0 0 4 4Z" />
                <path d="M5 10.5a7 7 0 0 0 14 0" />
                <path d="M12 17.5V21" />
                <path d="M8.5 21h7" />
              </svg>
              <span>发送</span>
            </div>
          </div>
        </div>
      </section>

      <section id="insights" class="section insight-section scroll-follow follow-medium">
        <div class="section-heading align-left wide-heading reveal-on-scroll">
          <span class="eyebrow">数据洞察</span>
          <h2>把心理状态转化为可理解的趋势</h2>
          <p>下方数据来自平台后端，用于呈现情绪变化、压力来源、预警数量和资源更新情况。</p>
        </div>

        <div v-if="loading" class="data-loading">正在从后端加载数据...</div>
        <template v-else>
          <div class="data-metrics">
            <article class="scroll-converge" v-bind="motionAttrs(0, 4, 100)">
              <span>学生档案</span>
              <strong>{{ dashboard?.stats.students ?? 0 }}</strong>
            </article>
            <article class="scroll-converge" v-bind="motionAttrs(1, 4, 100)">
              <span>咨询师</span>
              <strong>{{ dashboard?.stats.counselors ?? 0 }}</strong>
            </article>
            <article class="scroll-converge" v-bind="motionAttrs(2, 4, 100)">
              <span>心理资源</span>
              <strong>{{ dashboard?.stats.articles ?? 0 }}</strong>
            </article>
            <article class="warning scroll-converge" v-bind="motionAttrs(3, 4, 100)">
              <span>未处理预警</span>
              <strong>{{ dashboard?.stats.unhandled_alerts ?? 0 }}</strong>
            </article>
          </div>

          <div class="chart-grid">
            <article class="data-panel scroll-converge reveal-on-scroll" v-bind="motionAttrs(0, 2, 135)">
              <h3>情绪与睡眠趋势</h3>
              <div ref="trendChartRef" class="chart-box"></div>
            </article>
            <article class="data-panel scroll-converge reveal-on-scroll" v-bind="motionAttrs(1, 2, 135)">
              <h3>压力来源雷达图</h3>
              <div ref="pressureChartRef" class="chart-box"></div>
            </article>
          </div>
        </template>
        <button class="more-link" type="button" @click="navigate('insights')">&gt;&gt;&gt;进入数据洞察专题页</button>
      </section>

      <section id="support" class="section support-section scroll-follow follow-deep">
        <div class="section-heading align-left wide-heading reveal-on-scroll">
          <span class="eyebrow">专业对接</span>
          <h2>基于学生偏好与压力来源推荐咨询师</h2>
          <p>系统根据学生压力来源、关注主题与咨询师擅长领域智能计算匹配度，推荐最适合的心理咨询师。</p>
        </div>

        <div class="compact-list support-list">
          <article
            v-for="(counselor, index) in homeCounselors"
            :key="counselor.id"
            class="counselor-row scroll-converge"
            v-bind="motionAttrs(index, homeCounselors.length, 82)"
            @click="navigate('appointment')"
          >
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
        <div class="section-heading align-left wide-heading reveal-on-scroll">
          <span class="eyebrow">心理资源</span>
          <h2>科普文章与自助干预内容动态更新</h2>
        </div>

        <div class="compact-list resource-list">
          <article
            v-for="(article, index) in homeArticles"
            :key="article.id"
            class="resource-row scroll-converge"
            v-bind="motionAttrs(index, homeArticles.length, 78)"
            @click="openArticle(article)"
          >
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
        <div class="section-heading align-left wide-heading reveal-on-scroll">
          <span class="eyebrow">功能简介</span>
          <h2>按模块进入对应功能页</h2>
          <p>点击任一功能卡片进入对应页面，根据当前角色进行浏览、提交或管理操作。</p>
        </div>

        <div class="module-intro-grid">
          <article
            v-for="(intro, index) in moduleIntros"
            :key="intro.page"
            :class="['module-intro-card', 'scroll-converge', 'reveal-on-scroll', { 'alert-priority': intro.page === 'alerts' }]"
            v-bind="motionAttrs(index, moduleIntros.length, 104)"
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

      <section id="contact" class="cta-section scroll-follow follow-deep">
        <div>
          <span class="eyebrow">开始使用</span>
          <h2>进入平台，建立属于校园的心理支持空间</h2>
          <p>平台已全面上线，支持情绪打卡、匿名树洞、心理测评、咨询预约与预警管理等完整功能，为校园心理健康保驾护航。</p>
        </div>
        <div class="cta-actions">
          <template v-if="!currentUser">
            <button class="solid-button large" type="button" @click="openAuth('login')">登录平台</button>
            <button class="outline-button large" type="button" @click="openAuth('register')">创建账号</button>
          </template>
          <template v-else>
            <button class="solid-button large" type="button" @click="scrollToModules">查看功能</button>
            <button class="outline-button large" type="button" @click="navigate('profile')">个人资料</button>
          </template>
        </div>
      </section>
    </main>

    <main v-else class="standalone-page">
      <section v-if="currentPage !== 'ai-chat'" class="page-hero reveal-on-scroll">
        <button class="text-button" type="button" @click="navigate('home')">返回首页</button>
        <span class="eyebrow">{{ pageTitles[currentPage] }}</span>
        <h1>{{ pageTitles[currentPage] }}</h1>
      </section>

      <section v-if="currentPage === 'insights'" class="insights-page module-panel page-panel reveal-on-scroll">
        <div class="insights-toolbar">
          <div>
            <span class="eyebrow">开放数据看板</span>
            <h2>数据洞察专题页</h2>
            <p>集中查看情绪、压力、测评风险和咨询预约数据；下载与导出仅面向教师和管理员开放。</p>
          </div>
          <div v-if="canDownloadInsights" class="insight-actions">
            <button type="button" @click="downloadInsightCharts">下载图表</button>
            <button type="button" @click="downloadInsightExport('csv')">导出 CSV</button>
            <button class="solid-button" type="button" @click="downloadInsightExport('excel')">导出 Excel</button>
          </div>
        </div>

        <p v-if="insightMessage" class="module-message">{{ insightMessage }}</p>

        <template v-if="insightData">
          <div class="data-metrics insight-summary">
            <article>
              <span>学生档案</span>
              <strong>{{ insightData.summary.students }}</strong>
            </article>
            <article>
              <span>情绪记录</span>
              <strong>{{ insightData.summary.mood_entries }}</strong>
            </article>
            <article>
              <span>测评记录</span>
              <strong>{{ insightData.summary.assessment_records }}</strong>
            </article>
            <article class="warning">
              <span>未处理预警</span>
              <strong>{{ insightData.summary.unhandled_alerts }}</strong>
            </article>
          </div>

          <div class="chart-grid insight-chart-grid">
            <article class="data-panel">
              <div class="panel-head">
                <h3>情绪与睡眠趋势</h3>
                <button v-if="canDownloadInsights" type="button" @click="downloadChart(trendChart, '情绪与睡眠趋势.png')">下载</button>
              </div>
              <div ref="trendChartRef" class="chart-box"></div>
            </article>
            <article class="data-panel">
              <div class="panel-head">
                <h3>压力来源雷达图</h3>
                <button v-if="canDownloadInsights" type="button" @click="downloadChart(pressureChart, '压力来源雷达图.png')">下载</button>
              </div>
              <div ref="pressureChartRef" class="chart-box"></div>
            </article>
            <article class="data-panel">
              <div class="panel-head">
                <h3>风险等级分布</h3>
                <button v-if="canDownloadInsights" type="button" @click="downloadChart(riskChart, '风险等级分布.png')">下载</button>
              </div>
              <div ref="riskChartRef" class="chart-box"></div>
            </article>
            <article class="data-panel">
              <div class="panel-head">
                <h3>预约状态分布</h3>
                <button v-if="canDownloadInsights" type="button" @click="downloadChart(appointmentChart, '预约状态分布.png')">下载</button>
              </div>
              <div ref="appointmentChartRef" class="chart-box"></div>
            </article>
          </div>

          <div class="insight-table-grid">
            <section>
              <h3>近期情绪记录</h3>
              <table>
                <thead><tr><th>学生</th><th>情绪</th><th>强度</th><th>睡眠</th><th>压力来源</th><th>时间</th></tr></thead>
                <tbody>
                  <tr v-for="row in insightData.mood_rows.slice(0, 8)" :key="`mood-${row.student}-${row.created_at}`">
                    <td>{{ row.student }}</td><td>{{ row.mood }}</td><td>{{ row.intensity }}</td><td>{{ row.sleep_quality }}</td><td>{{ row.pressure_sources || '暂无' }}</td><td>{{ row.created_at }}</td>
                  </tr>
                </tbody>
              </table>
            </section>
            <section>
              <h3>近期测评记录</h3>
              <table>
                <thead><tr><th>学生</th><th>量表</th><th>分数</th><th>风险</th><th>时间</th></tr></thead>
                <tbody>
                  <tr v-for="row in insightData.assessment_rows.slice(0, 8)" :key="`assessment-${row.student}-${row.created_at}`">
                    <td>{{ row.student }}</td><td>{{ row.scale }}</td><td>{{ row.score }}</td><td>{{ row.risk_level }}</td><td>{{ row.created_at }}</td>
                  </tr>
                </tbody>
              </table>
            </section>
          </div>
        </template>
      </section>

      <section v-if="currentPage === 'register'" class="register-page module-panel page-panel">
        <div class="register-heading">
          <div class="auth-role-switch" aria-label="注册身份切换">
            <button type="button" :class="{ active: activeAuthRole === 'student' }" @click="setAuthRole('student')">学生注册</button>
            <button type="button" :class="{ active: activeAuthRole === 'teacher' }" @click="setAuthRole('teacher')">教师注册</button>
          </div>
          <span class="eyebrow">{{ activeAuthRoleLabel }}账号</span>
          <h2>{{ activeRegisterTitle }}</h2>
          <p>{{ activeAuthRole === 'student' ? '这些信息会写入学生档案，用于后续情绪记录、测评、咨询预约和资源推荐。' : '教师和管理员账号需要使用已锁定的邀请码完成注册。' }}</p>
        </div>

        <form class="register-form" @submit.prevent="submitRegister">
          <div class="registration-grid">
            <label>账号<input v-model.trim="authForm.username" maxlength="20" placeholder="用于登录的账号" required /></label>
            <label>姓名<input v-model.trim="authForm.name" maxlength="12" placeholder="真实姓名或常用称呼" /></label>
            <label>邮箱<input v-model.trim="authForm.email" type="email" placeholder="用于联系和通知" /></label>
            <label>密码<input v-model="authForm.password" minlength="8" pattern="(?=.*[a-z])(?=.*[A-Z]).{8,}" placeholder="至少8位，含大小写字母" type="password" required /></label>
            <label>确认密码<input v-model="authForm.confirmPassword" placeholder="再次输入密码" type="password" required /></label>
            <label v-if="activeAuthRole !== 'student'">邀请码<input v-model.trim="authForm.invitationCode" placeholder="请输入对应身份邀请码" required /></label>

            <template v-if="authForm.role === '学生'">
              <label>学号<input v-model.trim="authForm.studentNo" maxlength="50" placeholder="学生档案唯一编号" required /></label>
              <label>学院<input v-model.trim="authForm.college" placeholder="所在学院" /></label>
              <label>年级<input v-model.trim="authForm.grade" maxlength="4" inputmode="numeric" pattern="\d{4}" placeholder="例如：2023" /></label>
              <label>压力来源<input v-model="authForm.pressureSources" placeholder="用逗号分隔，每项不超过20字" /></label>
              <label class="full">关注主题<input v-model="authForm.preferredTopics" placeholder="用逗号分隔，如焦虑调节、时间管理、咨询预约" /></label>
              <label class="consent full">
                <input v-model="authForm.privacyConsent" type="checkbox" />
                <span>同意平台在校内心理支持场景下保存并使用以上信息</span>
              </label>
            </template>

            <template v-if="authForm.role === '心理老师'">
              <label>教师职称<input v-model.trim="authForm.teacherTitle" placeholder="例如：国家二级心理咨询师" /></label>
              <label>咨询标签<input v-model="authForm.teacherSpecialties" placeholder="用逗号分隔，如情绪调节、压力管理、睡眠" /></label>
              <label class="full">资质说明<textarea v-model="authForm.teacherQualifications" placeholder="填写咨询资质、擅长方向或值班说明"></textarea></label>
            </template>
          </div>

          <p v-if="authMessage" class="auth-message">{{ authMessage }}</p>
          <div class="register-actions">
            <button class="solid-button large" type="submit" :disabled="authSubmitting">
              {{ authSubmitting ? '提交中...' : '完成注册' }}
            </button>
            <button class="text-button" type="button" @click="openAuth('login')">已有账号，去登录</button>
          </div>
          <button class="admin-entry-button register-admin-entry" type="button" @click="setAuthRole('admin')">管理员</button>
        </form>
      </section>

      <section v-if="currentPage === 'profile'" class="profile-page module-panel page-panel">
        <div class="register-heading">
          <span class="eyebrow">账号设置</span>
          <h2>编辑个人资料</h2>
          <p>这些信息会用于平台展示、咨询预约和后续支持记录。</p>
        </div>

        <form v-if="currentUser" class="register-form" @submit.prevent="submitUserProfile">
          <div class="registration-grid">
            <label>姓名<input v-model.trim="profileForm.name" maxlength="12" required /></label>
            <label>邮箱<input v-model.trim="profileForm.email" type="email" /></label>

            <template v-if="currentRole === 'student'">
              <label>学院<input v-model.trim="profileForm.college" /></label>
              <label>年级<input v-model.trim="profileForm.grade" maxlength="4" inputmode="numeric" pattern="\d{4}" placeholder="例如：2023" /></label>
              <label>压力来源<input v-model="profileForm.pressure_sources" placeholder="用逗号分隔，每项不超过20字" /></label>
              <label class="full">关注主题<input v-model="profileForm.preferred_topics" placeholder="用逗号分隔，如焦虑调节、时间管理、咨询预约" /></label>
              <label class="consent full">
                <input v-model="profileForm.privacy_consent" type="checkbox" />
                <span>同意平台在校内心理支持场景下保存并使用以上信息</span>
              </label>
            </template>

            <template v-if="currentRole === 'teacher'">
              <label>职称<input v-model.trim="profileForm.title" placeholder="例如：国家二级心理咨询师" /></label>
              <label>咨询标签<input v-model="profileForm.specialties" placeholder="用逗号分隔，如情绪调节、压力管理、睡眠" /></label>
              <label class="full">资质说明<textarea v-model="profileForm.qualifications"></textarea></label>
              <label class="full">可预约时段<textarea v-model="profileForm.available_slots" placeholder="用逗号分隔，如周一下午、周三上午"></textarea></label>
            </template>
          </div>

          <p v-if="profileMessage" class="auth-message">{{ profileMessage }}</p>
          <div class="register-actions">
            <button class="solid-button large" type="submit">保存资料</button>
          </div>
        </form>

        <section v-if="targetInvitationRoles.length" class="invitation-panel" aria-label="邀请码管理">
          <div class="invitation-heading">
            <h3>邀请码管理</h3>
            <p>输入指定邀请码或随机生成后，点击锁定按钮保存并复制。右键邀请码区域可再次复制。</p>
          </div>
          <div class="invitation-grid">
            <article
              v-for="item in targetInvitationRoles"
              :key="item.role"
              class="invitation-card"
              :class="{ locked: invitationLocks[item.role] }"
              @click="copyLockedInvitation(item.role, $event)"
              @contextmenu.prevent="copyInvitation(item.role, $event)"
            >
              <div>
                <strong>{{ item.label }}</strong>
              </div>
              <div class="invitation-control">
                <input v-model.trim="invitationDrafts[item.role]" placeholder="输入邀请码" :disabled="invitationLocks[item.role]" @input="invitationLocks[item.role] = false" />
                <button class="icon-button lock-button" type="button" :title="invitationLocks[item.role] ? '解锁后修改邀请码' : '锁定并复制邀请码'" :aria-label="invitationLocks[item.role] ? `解锁${item.label}` : `锁定${item.label}`" @click.stop="lockInvitation(item.role, $event)">
                  <span class="lock-icon" :class="{ unlocked: !invitationLocks[item.role] }" aria-hidden="true"></span>
                </button>
              </div>
              <button class="outline-button invitation-generate" type="button" :disabled="invitationLocks[item.role]" @click.stop="generateInvitation(item.role)">随机生成</button>
            </article>
          </div>
        </section>
      </section>

      <section v-if="currentPage === 'ai-chat'" class="ai-chat-page module-panel page-panel reveal-on-scroll">
        <div class="ai-chat-layout">
          <aside class="ai-chat-side">
            <div class="ai-companion-card">
              <div class="ai-signal-mark" aria-hidden="true">
                <i></i>
                <i></i>
                <i></i>
              </div>
              <span class="eyebrow">实时陪伴</span>
              <h2>心晴正在倾听</h2>
              <p>说出此刻最明显的感受，平台会用温和的方式陪你梳理压力，并给出短时可执行的调节建议。</p>
            </div>

            <form v-if="currentRole === 'admin'" class="ai-config-panel" @submit.prevent="saveAiChatConfig">
              <div class="ai-config-head">
                <strong>管理员配置 API Key</strong>
                <span>{{ aiConfigForm.configured ? `已配置：${aiConfigForm.api_key_masked}` : '尚未配置' }}</span>
              </div>
              <label class="ai-config-toggle">
                <input v-model="aiConfigForm.enabled" type="checkbox" />
                <span>启用 AI 倾听</span>
              </label>
              <label>API Key
                <input v-model.trim="aiConfigForm.api_key" type="password" autocomplete="off" placeholder="输入新的 API Key；留空则保留原 Key" />
              </label>
              <div class="ai-provider-tabs" aria-label="AI 服务商预设">
                <button
                  v-for="preset in aiProviderPresets"
                  :key="preset.id"
                  :class="{ active: aiConfigForm.provider === preset.id }"
                  type="button"
                  @click="selectAiProvider(preset.id)"
                >
                  {{ preset.name }}
                </button>
              </div>
              <label>API 地址
                <input v-model.trim="aiConfigForm.api_url" placeholder="https://api.openai.com/v1/chat/completions" />
              </label>
              <p class="ai-config-hint">当前接口使用 OpenAI Chat Completions 格式。DeepSeek 请使用 /chat/completions，不要填写 /anthropic。</p>
              <label class="ai-config-toggle">
                <input v-model="aiConfigForm.auto_detect_model" type="checkbox" />
                <span>自动检测并选择模型</span>
              </label>
              <div class="ai-config-row">
                <label>模型
                  <input v-model.trim="aiConfigForm.model" :disabled="aiConfigForm.auto_detect_model" placeholder="gpt-4o-mini" />
                </label>
                <label>超时秒数
                  <input v-model.number="aiConfigForm.timeout" type="number" min="5" max="120" />
                </label>
              </div>
              <p v-if="aiConfigMessage" class="ai-config-message">{{ aiConfigMessage }}</p>
              <button class="solid-button" type="submit" :disabled="aiConfigSaving || aiConfigLoading">
                {{ aiConfigSaving ? '保存中...' : '保存配置' }}
              </button>
            </form>
          </aside>

          <section class="ai-chat-box" aria-label="AI 倾听对话窗口">
            <div class="ai-chat-toolbar">
              <span>当前对话</span>
              <button class="outline-button" type="button" @click="clearAiChat">新对话</button>
            </div>
            <div class="ai-chat-support">
              <strong>必要时优先联系真人支持</strong>
              <span>如有自伤、自杀、被伤害或伤害他人的紧急风险，请立刻联系学校心理中心、辅导员、身边可信任的人或当地紧急援助渠道。</span>
            </div>
            <div class="ai-chat-dialog-shell">
              <div ref="aiChatWindowRef" class="ai-chat-messages">
                <article
                  v-for="(message, index) in aiChatMessages"
                  :key="`${message.role}-${index}`"
                  :class="['ai-chat-bubble', message.role]"
                >
                  <span>{{ message.role === 'user' ? '我' : 'AI' }}</span>
                  <p>{{ message.content }}</p>
                </article>
                <article v-if="aiChatSending" class="ai-chat-bubble assistant pending">
                  <span>心晴</span>
                  <p>
                    心晴正在整理回应
                    <span class="typing-dots" aria-hidden="true"><i></i><i></i><i></i></span>
                  </p>
                </article>
              </div>

              <p v-if="aiChatMessage" class="module-message ai-chat-alert">{{ aiChatMessage }}</p>
              <div v-if="canUseAiChat" class="ai-chat-divider" aria-hidden="true"><span></span><strong></strong><span></span></div>
              <form v-if="canUseAiChat" class="ai-chat-composer" @submit.prevent="sendAiChatMessage">
                <textarea
                  v-model="aiChatInput"
                  maxlength="1200"
                  placeholder="写下你现在的感受、压力来源或想聊的事情"
                  @keydown.enter.exact.prevent="sendAiChatMessage"
                ></textarea>
                <div class="ai-voice-tools">
                  <button
                    :class="['ai-voice-button', { active: aiSpeechListening }]"
                    type="button"
                    :aria-label="aiSpeechListening ? '停止语音转文字' : '语音转文字'"
                    :title="aiSpeechListening ? '停止语音转文字' : '语音转文字'"
                    :aria-pressed="aiSpeechListening"
                    :disabled="aiChatSending || !aiSpeechSupported"
                    @click="toggleAiSpeechInput"
                  >
                    <svg class="ai-voice-icon" aria-hidden="true" viewBox="0 0 24 24" focusable="false">
                      <path d="M12 14.5a4 4 0 0 0 4-4V6a4 4 0 0 0-8 0v4.5a4 4 0 0 0 4 4Z" />
                      <path d="M5 10.5a7 7 0 0 0 14 0" />
                      <path d="M12 17.5V21" />
                      <path d="M8.5 21h7" />
                    </svg>
                  </button>
                </div>
                <button class="solid-button large" type="submit" :disabled="aiChatSending || !aiChatInput.trim()">
                  {{ aiChatSending ? '发送中...' : '发送' }}
                </button>
              </form>
            </div>
          </section>
        </div>
      </section>

      <section v-if="currentPage === 'details'" class="detail-page reveal-on-scroll">
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
              <button class="outline-button" type="button" @click="navigate(item.page)">进入模块</button>
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

      <section v-if="currentPage === 'mood'" class="page-panel mood-page reveal-on-scroll">
        <form v-if="canWrite" class="module-form mood-form" @submit.prevent="submitMood">
          <label>今日情绪<input v-model="moodForm.mood" /></label>
          <label>情绪强度<input v-model="moodForm.intensity" type="range" min="1" max="10" /></label>
          <label>睡眠质量<input v-model="moodForm.sleep_quality" type="range" min="1" max="10" /></label>
          <label>压力来源<input v-model="moodForm.pressure_sources" placeholder="用逗号分隔，每项不超过20字" /></label>
          <label class="full">日记<textarea v-model="moodForm.note"></textarea></label>
          <button class="solid-button large" type="submit">保存打卡</button>
        </form>
        <p v-if="moduleMessage" class="module-message">{{ moduleMessage }}</p>
        <div v-if="moodItems.length" class="section-block">
          <div class="section-label"><span>打卡记录</span><em>{{ moodItems.length }} 条</em></div>
          <div class="mood-list">
            <article v-for="(item, idx) in pagedMoods" :key="item.id" :class="{ alt: idx % 2 === 1 }">
              <div class="mood-row-main">
                <strong>{{ item.student_name }}</strong>
                <span class="mood-tag">{{ item.mood }}</span>
                <small>强度 {{ item.intensity }}/10 · 睡眠 {{ item.sleep_quality }}/10</small>
              </div>
              <p v-if="item.note">{{ item.note }}</p>
              <button v-if="canManage" class="danger-button compact" type="button" @click="adminDelete(`/api/mood-entries/${item.id}/`)">删除</button>
            </article>
          </div>
        </div>
        <div v-if="moodTotalPages > 1" class="pagination-bar">
          <button type="button" :disabled="moodPage <= 1" @click="changeMoodPage(moodPage - 1)">上一页</button>
          <span>第 {{ moodPage }} / {{ moodTotalPages }} 页 · 共 {{ moodItems.length }} 条</span>
          <button type="button" :disabled="moodPage >= moodTotalPages" @click="changeMoodPage(moodPage + 1)">下一页</button>
        </div>
      </section>

      <section v-if="currentPage === 'treehole'" class="page-panel treehole-page reveal-on-scroll">
        <form v-if="canPublishTreehole" class="module-form treehole-form" @submit.prevent="submitTreehole">
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
        <div class="section-block">
          <div class="section-label"><span>树洞列表</span><em>{{ treeholeItems.length }} 条</em></div>
          <p v-if="treeholeLoading" class="data-loading">正在加载树洞...</p>
          <div v-else-if="treeholeItems.length" class="treehole-list">
            <article v-for="post in pagedTreeholes" :key="post.id" class="treehole-post" @click="openTreehole(post)">
              <div class="treehole-post-head">
                <span>{{ post.student_name }}</span>
                <small>{{ post.mood_tag || '未标记' }} · {{ treeholeCategoryLabel(post.category) }}</small>
                <small class="treehole-meta">{{ post.support_count || 0 }} 支持 · {{ (post.replies || []).length }} 回复</small>
              </div>
              <p>{{ post.content.slice(0, 140) }}{{ post.content.length > 140 ? '...' : '' }}</p>
              <div class="treehole-post-foot">
                <small>{{ formatDateTime(post.created_at) }}</small>
                <div class="treehole-foot-actions">
                  <button class="support-btn" type="button" @click.stop="supportTreehole(post.id, $event)" title="给 ta 一点支持">
                    ♥ {{ post.support_count || 0 }}
                  </button>
                  <button class="treehole-enter-btn" type="button" @click.stop="openTreehole(post)">查看详情 →</button>
                </div>
              </div>
            </article>
          </div>
          <p v-else class="empty-state">还没有人发布树洞，来做第一个倾诉的人吧。</p>
        </div>
        <div v-if="treeholeTotalPages > 1" class="pagination-bar">
          <button type="button" :disabled="treeholePage <= 1" @click="changeTreeholePage(treeholePage - 1)">上一页</button>
          <span>第 {{ treeholePage }} / {{ treeholeTotalPages }} 页 · 共 {{ treeholeItems.length }} 条</span>
          <button type="button" :disabled="treeholePage >= treeholeTotalPages" @click="changeTreeholePage(treeholePage + 1)">下一页</button>
        </div>
      </section>

      <section v-if="currentPage === 'assessment'" class="page-panel assessment-page reveal-on-scroll">
        <form v-if="canWrite" class="module-form assessment-form" @submit.prevent="submitAssessment">
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
        <div v-if="recordItems.length" class="section-block">
          <div class="section-label"><span>测评记录</span><em>{{ recordItems.length }} 条</em></div>
          <div class="record-list">
            <div v-for="(record, idx) in pagedRecords" :key="record.id" :class="['record-row', { alt: idx % 2 === 1 }]">
              <div class="record-main">
                <strong>{{ record.student_name }}</strong>
                <span class="record-scale">{{ record.scale_name }}</span>
                <span class="record-score">{{ record.score }} 分</span>
                <small>{{ riskLevelLabel(record.risk_level) }}风险</small>
              </div>
              <p v-if="record.suggestion">{{ record.suggestion }}</p>
              <button v-if="canManage" class="danger-button compact" type="button" @click="adminDelete(`/api/assessment-records/${record.id}/`)">删除</button>
            </div>
          </div>
        </div>
        <div v-if="recordTotalPages > 1" class="pagination-bar">
          <button type="button" :disabled="recordPage <= 1" @click="changeRecordPage(recordPage - 1)">上一页</button>
          <span>第 {{ recordPage }} / {{ recordTotalPages }} 页 · 共 {{ recordItems.length }} 条</span>
          <button type="button" :disabled="recordPage >= recordTotalPages" @click="changeRecordPage(recordPage + 1)">下一页</button>
        </div>
      </section>

      <section v-if="currentPage === 'appointment'" class="page-panel appointment-page reveal-on-scroll">
        <div v-if="currentRole === 'teacher'" class="appointment-board teacher-profile-board">
          <h4>教师个人资料</h4>
          <form class="module-form" @submit.prevent="submitTeacherProfile">
            <label>姓名<input v-model.trim="teacherProfileForm.name" maxlength="12" /></label>
            <label>职称<input v-model.trim="teacherProfileForm.title" placeholder="例如：国家二级心理咨询师" /></label>
            <label class="full">咨询标签<input v-model="teacherProfileForm.specialties" placeholder="用逗号分隔，如情绪调节、压力管理、睡眠" /></label>
            <label class="full">资质说明<textarea v-model="teacherProfileForm.qualifications"></textarea></label>
            <label class="full">可预约时段<textarea v-model="teacherProfileForm.available_slots" placeholder="用逗号分隔，如周一下午、周三上午"></textarea></label>
            <button class="solid-button large" type="submit">保存个人资料</button>
          </form>
          <p v-if="moduleMessage" class="module-message">{{ moduleMessage }}</p>
          <section v-if="targetInvitationRoles.length" class="invitation-panel compact-invitation" aria-label="教师邀请码管理">
            <div class="invitation-heading">
              <h4>教师邀请码</h4>
              <p>输入或随机生成后点击锁定按钮，系统会保存并复制邀请码。</p>
            </div>
            <div class="invitation-grid">
              <article
                v-for="item in targetInvitationRoles"
                :key="`appointment-${item.role}`"
                class="invitation-card"
                :class="{ locked: invitationLocks[item.role] }"
                @click="copyLockedInvitation(item.role, $event)"
                @contextmenu.prevent="copyInvitation(item.role, $event)"
              >
                <div>
                  <strong>{{ item.label }}</strong>
                </div>
                <div class="invitation-control">
                  <input v-model.trim="invitationDrafts[item.role]" placeholder="输入邀请码" :disabled="invitationLocks[item.role]" @input="invitationLocks[item.role] = false" />
                  <button class="icon-button lock-button" type="button" :title="invitationLocks[item.role] ? '解锁后修改邀请码' : '锁定并复制邀请码'" :aria-label="invitationLocks[item.role] ? `解锁${item.label}` : `锁定${item.label}`" @click.stop="lockInvitation(item.role, $event)">
                    <span class="lock-icon" :class="{ unlocked: !invitationLocks[item.role] }" aria-hidden="true"></span>
                  </button>
                </div>
                <button class="outline-button invitation-generate" type="button" :disabled="invitationLocks[item.role]" @click.stop="generateInvitation(item.role)">随机生成</button>
              </article>
            </div>
          </section>
        </div>

        <div v-if="canManage" class="appointment-board counselor-create-board">
          <h4>管理员：将学生添加为咨询师</h4>
          <p class="empty-state" style="margin-bottom:12px">选择一名尚未关联咨询师档案的学生，填写咨询师信息后即可将其添加至可预约咨询师列表。</p>
          <button class="outline-button" type="button" @click="loadStudentList" style="margin-bottom:12px">刷新学生列表</button>
          <form class="module-form" @submit.prevent="createCounselorFromStudent">
            <label>选择学生
              <select v-model="counselorCreateForm.student_id" @focus="loadStudentList">
                <option :value="null" disabled>请选择学生...</option>
                <option v-for="student in studentsWithoutCounselor" :key="student.id" :value="student.id">
                  {{ student.name || student.username }} ({{ student.student_no }}){{ student.college ? ' - ' + student.college : '' }}
                </option>
              </select>
            </label>
            <label>咨询师姓名<input v-model.trim="counselorCreateForm.name" maxlength="40" placeholder="对外展示的姓名" /></label>
            <label>职称/头衔<input v-model.trim="counselorCreateForm.title" placeholder="例如：国家二级心理咨询师" /></label>
            <label>擅长领域标签<input v-model="counselorCreateForm.specialties" placeholder="用逗号分隔，如情绪调节、压力管理、睡眠" /></label>
            <label class="full">资质说明<textarea v-model="counselorCreateForm.qualifications" placeholder="填写咨询资质、擅长方向或值班说明"></textarea></label>
            <label>可预约时段<input v-model="counselorCreateForm.available_slots" placeholder="用逗号分隔，如周一下午、周三上午" /></label>
            <label>头像色<input v-model="counselorCreateForm.avatar_color" type="color" /></label>
            <button class="solid-button large" type="submit" :disabled="counselorCreateLoading">
              {{ counselorCreateLoading ? '提交中...' : '添加为咨询师' }}
            </button>
          </form>
          <p v-if="counselorCreateMessage" class="module-message">{{ counselorCreateMessage }}</p>
        </div>

        <div class="appointment-board counselor-recommend-board">
          <div class="board-heading-row">
            <h4>推荐咨询师列表</h4>
            <input v-model.trim="counselorSearch" type="search" placeholder="搜索咨询师、标签或擅长方向" />
          </div>
          <div v-if="recommendedCounselors.length" class="counselor-recommend-list">
            <article v-for="item in pagedRecommendedCounselors" :key="`recommended-${item.id}`" :class="{ selected: appointmentForm.counselor === item.id }" @click="appointmentForm.counselor = item.id">
              <span class="counselor-avatar small" :style="{ background: item.avatar_color }">{{ item.name.slice(0, 1) }}</span>
              <div>
                <strong>{{ item.name }} · {{ item.title }}</strong>
                <p>{{ item.qualifications || '暂无资质说明' }}</p>
                <div class="tag-list compact-tags editable-tags teacher-inline-tags">
                  <span v-for="tag in item.specialties.slice(0, 5)" :key="tag">{{ tag }}</span>
                  <button class="tag-add-button" type="button" @click.stop="openTagPopup($event, 'counselor', item.id)">+</button>
                </div>
              </div>
              <em>{{ item.match_score || 72 }}%</em>
            </article>
          </div>
          <div v-if="recommendedCounselors.length > counselorPageSize" class="mini-pagination">
            <button type="button" :disabled="counselorPage <= 1" @click="changeCounselorPage(counselorPage - 1)">上一页</button>
            <span>{{ counselorPage }} / {{ counselorTotalPages }}</span>
            <button type="button" :disabled="counselorPage >= counselorTotalPages" @click="changeCounselorPage(counselorPage + 1)">下一页</button>
          </div>
          <p v-else class="empty-state">未找到匹配的咨询师。</p>
          <p v-if="tagSuggestionMessage" class="module-message">{{ tagSuggestionMessage }}</p>
        </div>

        <div class="appointment-board appointment-info-board">
          <h4>同学预约信息</h4>
          <div v-if="recentAppointments.length" class="appointment-strip">
            <article v-for="item in recentAppointments" :key="`strip-${item.id}`">
              <strong>{{ item.student_name }}</strong>
              <span>{{ item.counselor_name }}</span>
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
          <p v-if="hasMoreAppointments" class="appointment-more-hint">...</p>
          <p v-if="!recentAppointments.length" class="empty-state">暂无可展示的预约信息。</p>
        </div>

        <div v-if="canWrite" class="appointment-board appointment-form-board">
          <h4>学生咨询预约表</h4>
          <form class="module-form" @submit.prevent="submitAppointment">
            <label>咨询师
              <select v-model="appointmentForm.counselor">
                <option v-for="item in recommendedCounselors" :key="item.id" :value="item.id">{{ item.name }} · {{ item.title }}</option>
              </select>
            </label>
            <label>预约时间
              <div class="datetime-control">
                <input ref="appointmentTimeInput" v-model="appointmentForm.scheduled_at" type="datetime-local" :min="minAppointmentDateTime" required />
                <button type="button" @click="confirmAppointmentTime">确定</button>
              </div>
            </label>
            <label class="full">咨询主题<input v-model="appointmentForm.topic" required /></label>
            <label class="full">保密备注<textarea v-model="appointmentForm.confidential_note"></textarea></label>
            <button class="solid-button large" type="submit">提交预约</button>
          </form>
          <p v-if="moduleMessage" class="module-message">{{ moduleMessage }}</p>
        </div>
      </section>

      <section v-if="currentPage === 'resources'" class="module-panel page-panel reveal-on-scroll">
        <div class="resource-search-bar">
          <input v-model.trim="resourceSearch" type="search" placeholder="搜索文章标题、来源、分类或标签" />
          <span>优先展示与你的打卡、测评和树洞标签更相关的资源</span>
        </div>
        <div class="topic-resource-list">
          <article v-for="article in pagedArticles" :key="article.id" class="topic-resource-item">
            <h3 class="article-title-link" @click="openArticle(article)">{{ article.title }}</h3>
            <span>{{ article.category }} · {{ article.source }}</span>
            <p>{{ article.summary }}</p>
            <div class="tag-list compact-tags">
              <span v-for="tag in article.tags.slice(0, 4)" :key="tag">{{ tag }}</span>
            </div>
            <small v-if="article.related_tags?.length">关联：{{ article.related_tags.join('、') }}</small>
            <button v-if="canManage" class="danger-button" type="button" @click.stop="adminDelete(`/api/articles/${article.id}/`)">删除</button>
          </article>
        </div>
        <div class="pagination-bar">
          <button type="button" :disabled="resourcePage <= 1" @click="changeResourcePage(resourcePage - 1)">上一页</button>
          <span>第 {{ resourcePage }} / {{ resourceTotalPages }} 页 · 共 {{ articles.length }} 篇</span>
          <button type="button" :disabled="resourcePage >= resourceTotalPages" @click="changeResourcePage(resourcePage + 1)">下一页</button>
        </div>
      </section>

      <section v-if="currentPage === 'article'" class="article-detail module-panel page-panel reveal-on-scroll">
        <template v-if="currentArticle">
          <span class="eyebrow">{{ currentArticle.category }} · {{ currentArticle.source }}</span>
          <h2>{{ currentArticle.title }}</h2>
          <p class="article-summary">{{ currentArticle.summary }}</p>
          <div class="tag-list editable-tags">
            <span v-for="tag in currentArticle.tags" :key="tag">{{ tag }}</span>
            <button class="tag-add-button" type="button" @click="openTagPopup($event, 'article', currentArticle.id)">+</button>
          </div>
          <p v-if="tagSuggestionMessage" class="module-message">{{ tagSuggestionMessage }}</p>
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

      <section v-if="currentPage === 'alerts' && canViewAlerts" class="page-panel alerts-page reveal-on-scroll">
        <div v-if="alertItems.length" class="section-block">
          <div class="section-label"><span>预警列表</span><em>{{ alertItems.length }} 条 · {{ alertItems.filter(a => !a.handled).length }} 条待跟进</em></div>
          <div class="alert-list">
            <article v-for="alert in pagedAlerts" :key="alert.id" :class="['alert-card', 'compact', alert.level]">
              <div class="alert-card-main">
                <div class="alert-card-info">
                  <strong>{{ alert.student_name }}</strong>
                  <span class="alert-level-tag">{{ alertLevelLabel(alert.level) }}</span>
                  <small>{{ formatDateTime(alert.created_at) }}</small>
                  <small class="alert-status">{{ alert.handled ? '已处理' : '待跟进' }}</small>
                </div>
                <p>{{ alert.trigger }}</p>
              </div>
              <div class="alert-card-actions">
                <button type="button" @click="openAlertStudentDetail(alert)">详情</button>
                <template v-if="canManage">
                  <button type="button" @click="editAlert(alert)">{{ alert.handled ? '未处理' : '已处理' }}</button>
                  <button class="danger-button compact" type="button" @click="adminDelete(`/api/crisis-alerts/${alert.id}/`)">删除</button>
                </template>
              </div>
            </article>
          </div>
        </div>
        <div v-if="alertTotalPages > 1" class="pagination-bar">
          <button type="button" :disabled="alertPage <= 1" @click="changeAlertPage(alertPage - 1)">上一页</button>
          <span>第 {{ alertPage }} / {{ alertTotalPages }} 页 · 共 {{ alertItems.length }} 条</span>
          <button type="button" :disabled="alertPage >= alertTotalPages" @click="changeAlertPage(alertPage + 1)">下一页</button>
        </div>
        <a v-if="canManage" class="outline-link admin-link" :href="adminUrl" target="_blank" rel="noreferrer">进入后台管理</a>
      </section>

      <section v-if="currentPage === 'treehole-detail'" class="page-panel treehole-detail-page">
        <button class="text-button" type="button" @click="navigate('treehole')">← 返回树洞列表</button>
        <template v-if="currentTreehole">
          <article class="treehole-detail-card reveal-on-scroll">
            <div class="treehole-detail-head">
              <div class="treehole-detail-author">
                <span class="treehole-detail-avatar" :style="{ background: '#d85d73' }">{{ (currentTreehole.student_name || '匿').slice(0, 1) }}</span>
                <div>
                  <strong>{{ currentTreehole.student_name }}</strong>
                  <small>{{ formatDateTime(currentTreehole.created_at) }}</small>
                </div>
              </div>
              <div class="treehole-detail-tags">
                <span class="treehole-cat-tag">{{ treeholeCategoryLabel(currentTreehole.category) }}</span>
                <span v-if="currentTreehole.mood_tag" class="treehole-mood-tag">{{ currentTreehole.mood_tag }}</span>
                <span v-if="currentTreehole.risk_flag" class="treehole-risk-tag">⚠ 风险标记</span>
              </div>
            </div>

            <div class="treehole-detail-body">
              <p>{{ currentTreehole.content }}</p>
            </div>

            <div class="treehole-detail-stats">
              <button class="treehole-stat support-stat-btn" type="button" @click="supportTreehole(currentTreehole.id, $event)" title="给 ta 一点支持">
                <strong>{{ currentTreehole.support_count || 0 }}</strong>
                <span>支持 ♥</span>
              </button>
              <div class="treehole-stat">
                <strong>{{ (currentTreehole.replies || []).length }}</strong>
                <span>回复</span>
              </div>
            </div>
          </article>

          <div class="section-block">
            <div class="section-label"><span>全部回复</span><em>{{ (currentTreehole.replies || []).length }} 条</em></div>
            <div v-if="currentTreehole.replies?.length" class="treehole-reply-wall">
              <article v-for="reply in currentTreehole.replies" :key="reply.id" class="treehole-reply-bubble" :class="{ counselor: reply.is_counselor_reply }">
                <div class="reply-bubble-head">
                  <strong>{{ reply.responder_name }}</strong>
                  <small v-if="reply.is_counselor_reply" class="counselor-badge">咨询师</small>
                  <small>{{ formatDateTime(reply.created_at) }}</small>
                </div>
                <p>{{ reply.content }}</p>
              </article>
            </div>
            <p v-else class="empty-state">暂无回复，来做第一个回应的人吧。</p>
          </div>

          <form v-if="canReplyTreehole" class="treehole-reply-form" @submit.prevent="submitTreeholeReplyFromDetail">
            <textarea v-model="replyForms[`treehole-${currentTreeholeId}`]" placeholder="写下你想说的话，给予温和的支持..." maxlength="800" rows="3"></textarea>
            <button class="solid-button" type="submit" :disabled="!replyForms[`treehole-${currentTreeholeId}`]?.trim()">发送回复</button>
          </form>
          <p v-else class="module-message">{{ readonlyReason }}</p>
        </template>
        <template v-else>
          <div class="data-loading" style="margin-top:20px">正在加载树洞内容...</div>
        </template>
      </section>

      <section v-if="currentPage === 'alert-detail' && canViewAlerts" class="module-panel page-panel alert-detail-page reveal-on-scroll">
        <div class="alert-detail-header">
          <div>
            <span class="eyebrow">预警学生详情</span>
            <h3>{{ selectedStudentProfile?.name || selectedStudentProfile?.username || '正在加载学生信息' }}</h3>
            <p v-if="selectedStudentProfile">{{ selectedStudentProfile.college || '未填写学院' }} · {{ selectedStudentProfile.grade || '未填写年级' }} · 学号 {{ selectedStudentProfile.student_no }}</p>
          </div>
          <div class="admin-actions">
            <button type="button" @click="navigate('alerts')">返回预警列表</button>
            <button type="button" :disabled="alertDetailLoading" @click="loadAlertStudentDetail(currentAlertId)">刷新详情</button>
          </div>
        </div>

        <p v-if="alertDetailLoading" class="module-message">正在加载预警学生详情...</p>
        <p v-if="alertDetailMessage" class="module-message">{{ alertDetailMessage }}</p>

        <template v-if="selectedAlertDetail">
          <div class="alert-summary-strip">
            <article>
              <span>预警等级</span>
              <strong>{{ alertLevelLabel(selectedAlertDetail.alert.level) }}</strong>
            </article>
            <article>
              <span>触发原因</span>
              <strong>{{ selectedAlertDetail.alert.trigger }}</strong>
            </article>
            <article>
              <span>处理状态</span>
              <strong>{{ selectedAlertDetail.alert.handled ? '已处理' : '待跟进' }}</strong>
            </article>
          </div>

          <div class="student-profile-grid">
            <article>
              <span>隐私授权</span>
              <strong>{{ selectedStudentProfile?.privacy_consent ? '已授权' : '未授权' }}</strong>
            </article>
            <article>
              <span>压力来源</span>
              <strong>{{ formatList(selectedStudentProfile?.pressure_sources) }}</strong>
            </article>
            <article>
              <span>关注主题</span>
              <strong>{{ formatList(selectedStudentProfile?.preferred_topics) }}</strong>
            </article>
          </div>

          <div class="alert-detail-grid">
            <section>
              <h5>情绪打卡</h5>
              <article v-for="item in selectedAlertDetail.moods" :key="`mood-${item.id}`">
                <strong>{{ item.mood }} · 强度 {{ item.intensity }}/10 · 睡眠 {{ item.sleep_quality }}/10</strong>
                <span>{{ formatDateTime(item.created_at) }} · {{ formatList(item.pressure_sources) }}</span>
                <p>{{ item.note || '暂无日记内容' }}</p>
              </article>
              <p v-if="!selectedAlertDetail.moods?.length" class="empty-state">暂无情绪打卡记录。</p>
            </section>

            <section>
              <h5>发布的树洞</h5>
              <article v-for="post in selectedAlertDetail.treeholes" :key="`treehole-${post.id}`">
                <strong>{{ treeholeCategoryLabel(post.category) }} · {{ post.mood_tag || '未标记' }} · {{ post.risk_flag ? '有风险标记' : '无风险标记' }}</strong>
                <span>{{ formatDateTime(post.created_at) }}</span>
                <p>{{ post.content }}</p>
              </article>
              <p v-if="!selectedAlertDetail.treeholes?.length" class="empty-state">暂无树洞记录。</p>
            </section>

            <section>
              <h5>心理测评</h5>
              <article v-for="record in selectedAlertDetail.records" :key="`record-${record.id}`">
                <strong>{{ record.scale_name }} · {{ record.score }} 分 · {{ riskLevelLabel(record.risk_level) }}</strong>
                <span>{{ formatDateTime(record.created_at) }}</span>
                <p>{{ record.suggestion || '暂无建议' }}</p>
              </article>
              <p v-if="!selectedAlertDetail.records?.length" class="empty-state">暂无测评记录。</p>
            </section>

            <section>
              <h5>咨询预约</h5>
              <article v-for="item in selectedAlertDetail.appointments" :key="`appointment-${item.id}`">
                <strong>{{ item.counselor_name }} · {{ statusLabel(item.status) }}</strong>
                <span>{{ formatDateTime(item.scheduled_at) }}</span>
                <p>{{ item.topic }}{{ item.confidential_note ? `：${item.confidential_note}` : '' }}</p>
              </article>
              <p v-if="!selectedAlertDetail.appointments?.length" class="empty-state">暂无咨询预约。</p>
            </section>

            <section>
              <h5>心理资源浏览记录</h5>
              <article v-for="log in selectedAlertDetail.resource_views" :key="`resource-view-${log.id}`">
                <strong>{{ log.article_title }}</strong>
                <span>{{ log.article_category || '未分类' }} · {{ log.article_source || '未知来源' }} · {{ formatDateTime(log.created_at) }}</span>
              </article>
              <p v-if="!selectedAlertDetail.resource_views?.length" class="empty-state">暂无资源浏览记录。</p>
            </section>

            <section>
              <h5>历史预警</h5>
              <article v-for="item in selectedAlertDetail.alerts" :key="`alert-history-${item.id}`">
                <strong>{{ alertLevelLabel(item.level) }} · {{ item.handled ? '已处理' : '待跟进' }}</strong>
                <span>{{ formatDateTime(item.created_at) }}</span>
                <p>{{ item.trigger }}</p>
              </article>
            </section>
          </div>
        </template>
      </section>
    </main>

    <footer class="site-footer">
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
            <a href="#/home" @click.prevent="navigateHomeSection('home')">首页</a>
            <a href="#/home" @click.prevent="navigateHomeSection('features')">功能服务</a>
            <a href="#/home" @click.prevent="navigateHomeSection('scenes')">使用场景</a>
            <a href="#/home" @click.prevent="navigateHomeSection('contact')">联系我们</a>
            <a href="#/register" @click.prevent="openAuth('register')">加入我们</a>
            <a href="https://github.com/RorzAlkaid/P-support-E-expression" target="_blank" rel="noreferrer" class="footer-github-link" title="在 GitHub 上查看项目">GitHub</a>
          </nav>

          <p>
            健康提示：平台内容用于心理健康教育、自我记录和校园支持服务，不替代专业医疗诊断。如出现持续强烈痛苦、
            自伤想法或紧急风险，请立即联系学校心理中心、辅导员或当地紧急援助渠道。
          </p>
          <p>
            服务说明：情绪打卡、匿名表达、心理测评与咨询预约数据仅用于校园心理支持流程；平台倡导尊重、保密、及时响应的求助环境。
          </p>
          <p>
            所属学校：请在学校后台配置 ｜ 联系邮箱：请在学校后台配置 ｜ 联系电话：请在学校后台配置
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
        <div class="auth-role-switch" aria-label="登录身份切换">
          <button type="button" :class="{ active: activeAuthRole === 'student' }" @click="setAuthRole('student')">学生登录</button>
          <button type="button" :class="{ active: activeAuthRole === 'teacher' }" @click="setAuthRole('teacher')">教师登录</button>
        </div>
        <h2>{{ activeLoginTitle }}</h2>
        <p>请使用{{ activeAuthRoleLabel }}账号登录对应入口。</p>
        <form class="auth-form" @submit.prevent="submitAuth">
          <input v-model.trim="authForm.username" maxlength="20" placeholder="账号" required />
          <input v-model="authForm.password" placeholder="密码" type="password" required />
          <p v-if="authMessage" class="auth-message">{{ authMessage }}</p>
          <button class="solid-button large" type="submit" :disabled="authSubmitting">
            {{ authSubmitting ? '提交中...' : '登录' }}
          </button>
          <div class="auth-form-links">
            <button class="text-button" type="button" @click="openAuth('register')">没有账号，去注册</button>
          </div>
          <button class="admin-entry-button" type="button" @click="setAuthRole('admin')">管理员</button>
        </form>
      </section>
    </div>
  </div>
</template>
