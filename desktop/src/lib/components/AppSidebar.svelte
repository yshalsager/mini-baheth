<script lang='ts'>
  import { Sidebar, SidebarContent, SidebarHeader, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarSeparator } from '$lib/components/ui/sidebar'
  import DirectoryPicker from '$lib/components/DirectoryPicker.svelte'
  import FileFilterSelect from '$lib/components/FileFilterSelect.svelte'
  import { FILE_FILTERS } from '$lib/constants'

  let {
    directory_search = $bindable(''),
    directories = [],
    directories_loading = false,
    directories_error = '',
    selected_directory = $bindable(''),
    file_filter = $bindable(''),
    handle_directory_search,
    handle_directory_focus,
    handle_directory_value_change,
    handle_file_filter_change,
  }: {
    directory_search?: string
    directories?: string[]
    directories_loading?: boolean
    directories_error?: string
    selected_directory?: string
    file_filter?: string
    handle_directory_search: () => void
    handle_directory_focus: () => void
    handle_directory_value_change: (value: string) => void
    handle_file_filter_change: (value: string) => void
  } = $props()
</script>

<Sidebar side='left' collapsible='offcanvas' class='h-full'>
  <SidebarHeader class='text-right'>الإعدادات</SidebarHeader>
  <SidebarContent>
    <SidebarGroup>
      <SidebarGroupLabel>المجلدات</SidebarGroupLabel>
      <SidebarGroupContent>
        <DirectoryPicker
          bind:directory_search
          {directories}
          {directories_loading}
          {directories_error}
          bind:selected_directory
          {handle_directory_search}
          {handle_directory_focus}
          {handle_directory_value_change}
        />
      </SidebarGroupContent>
    </SidebarGroup>

    <SidebarSeparator />

    <SidebarGroup>
      <SidebarGroupLabel>نوع الملف</SidebarGroupLabel>
      <SidebarGroupContent>
        <FileFilterSelect bind:file_filter options={FILE_FILTERS} {handle_file_filter_change} />
      </SidebarGroupContent>
    </SidebarGroup>
  </SidebarContent>
</Sidebar>
