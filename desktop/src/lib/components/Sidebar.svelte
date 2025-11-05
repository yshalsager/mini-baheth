<script lang='ts'>
  import { ScrollArea } from '$lib/components/ui/scroll-area'
  import { Button } from '$lib/components/ui/button'
  import { Card } from '$lib/components/ui/card'

  let {
    data_root = '',
    selected_directory = '',
    file_filter = '',
    on_change_root
  }: {
    data_root?: string
    selected_directory?: string
    file_filter?: string
    on_change_root: () => void
  } = $props()
</script>

<aside class='h-full border-e bg-background/60'>
  <ScrollArea class='h-full'>
    <div class='flex flex-col gap-4 p-4 text-right'>
      <Card class='p-3'>
        <div class='flex items-center justify-between gap-2'>
          <h3 class='text-sm font-medium'>الجذر</h3>
          <Button size='sm' variant='outline' onclick={on_change_root}>تغيير</Button>
        </div>
        <p class='mt-2 truncate text-xs text-muted-foreground' dir='ltr'>{data_root || 'غير محدد'}</p>
      </Card>

      <Card class='p-3'>
        <h3 class='text-sm font-medium'>المجلد الحالي</h3>
        <p class='mt-2 truncate text-xs text-muted-foreground' dir='ltr'>{selected_directory || 'غير محدد'}</p>
      </Card>

      <Card class='p-3'>
        <h3 class='text-sm font-medium'>مرشح الملفات</h3>
        <p class='mt-2 truncate text-xs text-muted-foreground'>{file_filter}</p>
      </Card>
    </div>
  </ScrollArea>
</aside>

