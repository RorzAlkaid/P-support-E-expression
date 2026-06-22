<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import heroImage from './assets/landing-hero.png'
import logoMark from './assets/xinqing-logo-mark.svg'

const authMode = ref('login')
const showAuth = ref(false)
const inkX = ref('50vw')
const inkY = ref('28vh')
const inkActive = ref(0.38)
const scrollShift = ref('0px')

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

onMounted(() => {
  handleScroll()
  window.addEventListener('pointermove', handlePointerMove)
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('scroll', handleScroll)
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
  authMode.value = mode
  showAuth.value = true
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
      <a class="brand" href="#home" aria-label="心晴校园首页">
        <span class="brand-mark">
          <img :src="logoMark" alt="" />
        </span>
        <strong>心晴校园</strong>
      </a>

      <nav class="site-nav" aria-label="网站导航">
        <a href="#features">功能</a>
        <a href="#scenes">场景</a>
        <a href="#process">流程</a>
        <a href="#contact">开始使用</a>
      </nav>

      <div class="auth-actions">
        <button class="text-button" type="button" @click="openAuth('login')">登录</button>
        <button class="solid-button" type="button" @click="openAuth('register')">注册</button>
      </div>
    </header>

    <main>
      <section id="home" class="hero-section scroll-follow follow-soft">
        <div class="hero-copy reveal-up">
          <span class="eyebrow">大学生心理支持与情绪表达平台</span>
          <h1>让每一次情绪表达<br />都能被温柔接住</h1>
          <p>
            面向高校学生、心理老师与管理者的一体化平台，整合情绪打卡、匿名倾诉、心理测评、咨询预约和风险预警。
          </p>
          <div class="hero-actions">
            <button class="solid-button large" type="button" @click="openAuth('register')">立即体验</button>
            <a class="outline-link" href="#features">查看功能</a>
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
          <article v-for="feature in features" :key="feature.title" :class="['feature-card', feature.accent]" tabindex="0">
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

      <section id="contact" class="cta-section scroll-follow follow-deep">
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
          <button :class="{ active: authMode === 'login' }" type="button" @click="authMode = 'login'">登录</button>
          <button :class="{ active: authMode === 'register' }" type="button" @click="authMode = 'register'">注册</button>
        </div>
        <h2>{{ authMode === 'login' ? '欢迎回来' : '创建账号' }}</h2>
        <p>{{ authMode === 'login' ? '登录后进入学生端或教师端。' : '注册后可进行情绪记录、测评和预约。' }}</p>
        <form class="auth-form">
          <input placeholder="学号 / 工号 / 邮箱" />
          <input placeholder="密码" type="password" />
          <input v-if="authMode === 'register'" placeholder="确认密码" type="password" />
          <select v-if="authMode === 'register'">
            <option>学生</option>
            <option>心理老师</option>
            <option>管理员</option>
          </select>
          <button class="solid-button large" type="button">{{ authMode === 'login' ? '登录' : '注册' }}</button>
        </form>
      </section>
    </div>
  </div>
</template>
