(function () {
  if (typeof django === 'undefined' || typeof django.jQuery === 'undefined') {
    // SimpleUI or other admin themes may load jQuery differently
    document.addEventListener('DOMContentLoaded', initModelSwitcher)
    return
  }
  django.jQuery(document).ready(initModelSwitcher)

  function initModelSwitcher() {
    const $ = django.jQuery
    const providerField = $('#id_provider')
    const modelSelect = $('#id_model_select')
    const modelCustom = $('#id_model_custom')
    const autoDetect = $('#id_auto_detect_model')

    if (!providerField.length || !modelSelect.length) return

    // Model lists grouped by provider value
    const modelMap = {
      'openai': [
        { value: 'gpt-4o', label: 'gpt-4o' },
        { value: 'gpt-4o-mini', label: 'gpt-4o-mini' },
        { value: 'gpt-4-turbo', label: 'gpt-4-turbo' },
        { value: 'gpt-4', label: 'gpt-4' },
        { value: 'gpt-3.5-turbo', label: 'gpt-3.5-turbo' },
      ],
      'deepseek': [
        { value: 'deepseek-chat', label: 'deepseek-chat' },
        { value: 'deepseek-v4-flash', label: 'deepseek-v4-flash' },
        { value: 'deepseek-reasoner', label: 'deepseek-reasoner' },
        { value: 'deepseek-v4', label: 'deepseek-v4' },
      ],
      'auto': [
        { value: 'gpt-4o', label: 'gpt-4o (OpenAI)' },
        { value: 'gpt-4o-mini', label: 'gpt-4o-mini (OpenAI)' },
        { value: 'gpt-4-turbo', label: 'gpt-4-turbo (OpenAI)' },
        { value: 'gpt-4', label: 'gpt-4 (OpenAI)' },
        { value: 'gpt-3.5-turbo', label: 'gpt-3.5-turbo (OpenAI)' },
        { value: 'deepseek-chat', label: 'deepseek-chat (DeepSeek)' },
        { value: 'deepseek-v4-flash', label: 'deepseek-v4-flash (DeepSeek)' },
        { value: 'deepseek-reasoner', label: 'deepseek-reasoner (DeepSeek)' },
        { value: 'deepseek-v4', label: 'deepseek-v4 (DeepSeek)' },
      ],
      'custom': [
        { value: 'gpt-4o', label: 'gpt-4o (OpenAI 兼容)' },
        { value: 'gpt-4o-mini', label: 'gpt-4o-mini (OpenAI 兼容)' },
        { value: 'gpt-4-turbo', label: 'gpt-4-turbo (OpenAI 兼容)' },
        { value: 'gpt-4', label: 'gpt-4 (OpenAI 兼容)' },
        { value: 'gpt-3.5-turbo', label: 'gpt-3.5-turbo (OpenAI 兼容)' },
        { value: 'deepseek-chat', label: 'deepseek-chat (DeepSeek 兼容)' },
        { value: 'deepseek-v4-flash', label: 'deepseek-v4-flash (DeepSeek 兼容)' },
        { value: 'deepseek-reasoner', label: 'deepseek-reasoner (DeepSeek 兼容)' },
        { value: 'deepseek-v4', label: 'deepseek-v4 (DeepSeek 兼容)' },
      ],
    }

    const customOption = { value: '__custom__', label: '自定义模型...' }

    var currentModelValue = modelSelect.val()

    function updateModelOptions(provider) {
      var models = modelMap[provider] || modelMap['custom']
      var options = models.concat([customOption])
      var selected = modelSelect.val()

      modelSelect.empty()
      options.forEach(function (opt) {
        var $option = $('<option></option>').attr('value', opt.value).text(opt.label)
        modelSelect.append($option)
      })

      // Restore previous selection if still valid
      var newValues = options.map(function (o) { return o.value })
      if (newValues.indexOf(selected) >= 0) {
        modelSelect.val(selected)
      } else {
        modelSelect.val(options[0].value)
      }
    }

    function toggleModelFields() {
      var isAuto = autoDetect.length && autoDetect.is(':checked')
      var isCustom = modelSelect.val() === '__custom__'

      if (isAuto) {
        modelSelect.prop('disabled', true)
        modelSelect.css('opacity', '0.6')
        modelCustom.prop('disabled', true).val('').hide()
        if (modelCustom.next('.model-custom-hint').length === 0) {
          modelCustom.after($('<span class="model-custom-hint" style="color:#888;margin-left:8px;">自动检测已启用，模型将由系统自动选择</span>'))
        }
        modelCustom.next('.model-custom-hint').show()
      } else {
        modelSelect.prop('disabled', false)
        modelSelect.css('opacity', '1')
        modelCustom.next('.model-custom-hint').hide()
        if (isCustom) {
          modelCustom.show()
          modelCustom.prop('disabled', false)
        } else {
          modelCustom.hide()
          modelCustom.prop('disabled', true)
        }
      }
    }

    providerField.on('change', function () {
      updateModelOptions($(this).val())
      toggleModelFields()
    })

    modelSelect.on('change', function () {
      toggleModelFields()
    })

    if (autoDetect.length) {
      autoDetect.on('change', function () {
        toggleModelFields()
      })
    }

    // Initialize on page load
    updateModelOptions(providerField.val())
    toggleModelFields()
  }
})()
