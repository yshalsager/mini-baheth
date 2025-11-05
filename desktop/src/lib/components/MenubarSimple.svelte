<script lang='ts'>
  import { Button } from '$lib/components/ui/button'
  import { Separator } from '$lib/components/ui/separator'

  let {
    on_change_root,
    on_clear_query,
    on_toggle_wrap,
    on_font_inc,
    on_font_dec,
    on_open_help
  }: {
    on_change_root: () => void
    on_clear_query: () => void
    on_toggle_wrap: () => void
    on_font_inc: () => void
    on_font_dec: () => void
    on_open_help: () => void
  } = $props()

  let open_menu: 'file' | 'edit' | 'view' | 'help' | '' = $state('')
  function toggle(menu: typeof open_menu) {
    open_menu = open_menu === menu ? '' : menu
  }
</script>

<nav class='flex items-center gap-2 rounded border bg-background px-2 py-1 text-sm'>
  <div class='relative'>
    <Button variant='ghost' size='sm' onclick={() => toggle('file')}>ملف</Button>
    {#if open_menu === 'file'}
      <div class='absolute z-50 mt-1 min-w-40 rounded border bg-background p-1 shadow'>
        <button class='block w-full rounded px-3 py-1 text-right hover:bg-muted' onclick={() => { on_change_root(); open_menu = '' }}>تغيير الجذر</button>
      </div>
    {/if}
  </div>

  <div class='relative'>
    <Button variant='ghost' size='sm' onclick={() => toggle('edit')}>تحرير</Button>
    {#if open_menu === 'edit'}
      <div class='absolute z-50 mt-1 min-w-40 rounded border bg-background p-1 shadow'>
        <button class='block w-full rounded px-3 py-1 text-right hover:bg-muted' onclick={() => { on_clear_query(); open_menu = '' }}>مسح البحث</button>
      </div>
    {/if}
  </div>

  <div class='relative'>
    <Button variant='ghost' size='sm' onclick={() => toggle('view')}>عرض</Button>
    {#if open_menu === 'view'}
      <div class='absolute z-50 mt-1 min-w-48 rounded border bg-background p-1 shadow'>
        <button class='block w-full rounded px-3 py-1 text-right hover:bg-muted' onclick={() => { on_toggle_wrap(); open_menu = '' }}>تبديل التفاف السطور</button>
        <Separator />
        <div class='flex items-center justify-between gap-2 px-3 py-1'>
          <span>حجم الخط</span>
          <div class='flex items-center gap-1'>
            <Button size='icon' variant='outline' onclick={() => { on_font_dec(); open_menu = '' }}>−</Button>
            <Button size='icon' variant='outline' onclick={() => { on_font_inc(); open_menu = '' }}>+</Button>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <div class='relative'>
    <Button variant='ghost' size='sm' onclick={() => toggle('help')}>مساعدة</Button>
    {#if open_menu === 'help'}
      <div class='absolute z-50 mt-1 min-w-40 rounded border bg-background p-1 shadow'>
        <button class='block w-full rounded px-3 py-1 text-right hover:bg-muted' onclick={() => { on_open_help(); open_menu = '' }}>الدليل</button>
      </div>
    {/if}
  </div>
</nav>
