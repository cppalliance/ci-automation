/* GCOVR Custom JavaScript - Tree View & Interactivity */

(function() {
  'use strict';

  // Wait for DOM ready
  document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initSidebar();
    initFileTree();
    initBreadcrumbs();
    initSearch();
    initSorting();
    initToggleButtons();
    initTreeControls();
  });

  // ===========================================
  // Breadcrumb Links
  // ===========================================

  function initBreadcrumbs() {
    var currentSpan = document.querySelector('.breadcrumb .current');
    if (!currentSpan || !window.GCOVR_TREE_DATA) return;

    var pathText = currentSpan.textContent.trim();
    var segments = pathText.split(' / ');
    if (segments.length <= 1) return;

    // Auto-detect and skip prefix segments not in tree (e.g., "boost", "json")
    // Find the first segment that matches a root node in the tree
    var startIndex = 0;
    var rootNames = window.GCOVR_TREE_DATA.map(function(n) { return n.name; });
    for (var i = 0; i < segments.length; i++) {
      if (rootNames.indexOf(segments[i]) !== -1) {
        startIndex = i;
        break;
      }
    }
    // Skip prefix segments
    segments = segments.slice(startIndex);
    if (segments.length === 0) return;

    // Create linked breadcrumb by traversing tree
    var fragment = document.createDocumentFragment();
    var currentNodes = window.GCOVR_TREE_DATA;

    for (var i = 0; i < segments.length; i++) {
      var segment = segments[i];

      if (i > 0) {
        var sep = document.createElement('span');
        sep.className = 'separator';
        sep.textContent = '/';
        fragment.appendChild(sep);
      }

      // Find this segment in current level of tree
      var foundNode = null;
      for (var j = 0; j < currentNodes.length; j++) {
        if (currentNodes[j].name === segment) {
          foundNode = currentNodes[j];
          break;
        }
      }

      if (foundNode && foundNode.link && i < segments.length - 1) {
        // Directory segment with link - make it clickable
        var a = document.createElement('a');
        a.href = foundNode.link;
        a.textContent = segment;
        fragment.appendChild(a);
        // Move to children for next iteration
        currentNodes = foundNode.children || [];
      } else {
        // Last segment (current file) or no link found
        var span = document.createElement('span');
        span.className = 'current-file';
        span.textContent = segment;
        fragment.appendChild(span);
        if (foundNode && foundNode.children) {
          currentNodes = foundNode.children;
        }
      }
    }

    currentSpan.innerHTML = '';
    currentSpan.appendChild(fragment);
  }

  // ===========================================
  // Theme Toggle
  // ===========================================

  function initTheme() {
    const toggle = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('gcovr-theme');

    // Apply saved theme or default to dark
    if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme);
    }

    if (toggle) {
      toggle.addEventListener('click', function() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('gcovr-theme', next);
      });
    }
  }

  // ===========================================
  // Tree Controls (Expand/Collapse All)
  // ===========================================

  function initTreeControls() {
    var expandBtn = document.getElementById('expand-all');
    var collapseBtn = document.getElementById('collapse-all');

    if (expandBtn) {
      expandBtn.addEventListener('click', function() {
        document.querySelectorAll('.tree-item').forEach(function(item) {
          if (!item.classList.contains('no-children')) {
            item.classList.add('expanded');
            var toggle = item.querySelector(':scope > .tree-item-header > .tree-folder-toggle');
            if (toggle) toggle.textContent = '−';
          }
        });
      });
    }

    if (collapseBtn) {
      collapseBtn.addEventListener('click', function() {
        document.querySelectorAll('.tree-item').forEach(function(item) {
          item.classList.remove('expanded');
          var toggle = item.querySelector(':scope > .tree-item-header > .tree-folder-toggle');
          if (toggle) toggle.textContent = '+';
        });
      });
    }
  }

  // ===========================================
  // Sidebar Toggle
  // ===========================================

  function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');

    if (!sidebar || !toggle) return;

    // Load saved state
    const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (isCollapsed) {
      sidebar.classList.add('collapsed');
    }

    toggle.addEventListener('click', function() {
      sidebar.classList.toggle('collapsed');
      localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
    });

    // Mobile: open sidebar when clicked outside should close it
    document.addEventListener('click', function(e) {
      if (window.innerWidth <= 1024) {
        if (sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            e.target !== toggle &&
            !toggle.contains(e.target)) {
          sidebar.classList.remove('open');
        }
      }
    });

    // Mobile toggle
    toggle.addEventListener('click', function() {
      if (window.innerWidth <= 1024) {
        sidebar.classList.toggle('open');
      }
    });
  }

  // ===========================================
  // File Tree - Load from tree.json
  // ===========================================

  function initFileTree() {
    var treeContainer = document.getElementById('file-tree');
    if (!treeContainer) return;

    // Check for embedded tree data first (works for local file:// access)
    if (window.GCOVR_TREE_DATA) {
      renderTree(treeContainer, window.GCOVR_TREE_DATA);
      return;
    }

    // Fallback: try to load tree.json for full hierarchy
    fetch('tree.json')
      .then(function(response) {
        if (!response.ok) throw new Error('No tree.json');
        return response.json();
      })
      .then(function(tree) {
        renderTree(treeContainer, tree);
      })
      .catch(function(err) {
        console.log('tree.json not found, using static sidebar');
        // Keep existing static content from Jinja template
      });
  }

  function renderTree(container, tree) {
    container.innerHTML = '';

    if (!tree || tree.length === 0) {
      container.innerHTML = '<div class="tree-loading">No files found</div>';
      return;
    }

    tree.forEach(function(item) {
      container.appendChild(createTreeItem(item));
    });

    // Auto-expand to current file and highlight it
    expandToCurrentFile(container);
  }

  function expandToCurrentFile(container) {
    // Get current page filename
    var currentPage = window.location.pathname.split('/').pop() || 'index.html';

    // Find the link matching current page
    var currentLink = container.querySelector('a[href="' + currentPage + '"]');
    if (!currentLink) return;

    // Mark as active
    var treeItem = currentLink.closest('.tree-item');
    if (treeItem) {
      treeItem.classList.add('active');
    }

    // Expand all parent folders
    var parent = currentLink.closest('.tree-children');
    while (parent) {
      var parentItem = parent.closest('.tree-item');
      if (parentItem) {
        parentItem.classList.add('expanded');
        var toggle = parentItem.querySelector(':scope > .tree-item-header > .tree-folder-toggle');
        if (toggle) toggle.textContent = '−';
      }
      parent = parentItem ? parentItem.parentElement.closest('.tree-children') : null;
    }

    // Scroll into view
    if (currentLink) {
      currentLink.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }

  function createTreeItem(item) {
    var hasChildren = item.children && item.children.length > 0;
    var isDirectory = item.isDirectory || hasChildren;

    var div = document.createElement('div');
    div.className = 'tree-item' + (isDirectory ? ' is-folder' : '') + (hasChildren ? '' : ' no-children');

    var header = document.createElement('div');
    header.className = 'tree-item-header';
    var toggle = null;

    // Toggle button (+/-) for folders with children
    if (hasChildren) {
      toggle = document.createElement('button');
      toggle.className = 'tree-folder-toggle';
      toggle.textContent = '+';
      toggle.setAttribute('aria-label', 'Toggle folder');
      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        e.preventDefault();
        var isExpanded = div.classList.toggle('expanded');
        toggle.textContent = isExpanded ? '−' : '+';
      });
      header.appendChild(toggle);

      // Make entire header clickable to expand/collapse
      header.style.cursor = 'pointer';
      header.addEventListener('click', function(e) {
        // Don't toggle if clicking a link
        if (e.target.tagName === 'A') return;
        e.preventDefault();
        var isExpanded = div.classList.toggle('expanded');
        toggle.textContent = isExpanded ? '−' : '+';
      });
    } else {
      var spacer = document.createElement('span');
      spacer.className = 'tree-spacer';
      header.appendChild(spacer);
    }

    // Icon - different for folders vs files
    var icon = document.createElement('span');
    if (isDirectory) {
      icon.className = 'tree-icon tree-icon-folder';
      icon.innerHTML = '<svg viewBox="0 0 16 16" width="16" height="16"><path fill="currentColor" d="M1.75 1A1.75 1.75 0 000 2.75v10.5C0 14.216.784 15 1.75 15h12.5A1.75 1.75 0 0016 13.25v-8.5A1.75 1.75 0 0014.25 3H7.5a.25.25 0 01-.2-.1l-.9-1.2C6.07 1.26 5.55 1 5 1H1.75z"/></svg>';
    } else {
      icon.className = 'tree-icon tree-icon-file';
      icon.innerHTML = '<svg viewBox="0 0 16 16" width="16" height="16"><path fill="currentColor" d="M3.75 1.5a.25.25 0 00-.25.25v12.5c0 .138.112.25.25.25h9.5a.25.25 0 00.25-.25V6h-2.75A1.75 1.75 0 019 4.25V1.5H3.75zm6.75.062V4.25c0 .138.112.25.25.25h2.688l-2.938-2.938zM2 1.75C2 .784 2.784 0 3.75 0h6.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v9.586A1.75 1.75 0 0113.25 16h-9.5A1.75 1.75 0 012 14.25V1.75z"/></svg>';
    }
    header.appendChild(icon);

    // Label (with link if available)
    // Use fullPath for tooltip if available, otherwise use name
    var tooltipText = item.fullPath || item.name;
    var label = document.createElement('span');
    label.className = 'tree-label';
    // Apply coverage class for coloring
    if (item.coverageClass) {
      label.classList.add(item.coverageClass);
    }
    label.title = tooltipText;
    if (item.link) {
      var link = document.createElement('a');
      link.href = item.link;
      link.textContent = item.name;
      link.title = tooltipText;
      label.appendChild(link);
    } else {
      label.textContent = item.name;
    }
    header.appendChild(label);

    div.appendChild(header);

    // Children container (for expand/collapse)
    if (hasChildren) {
      var childrenWrapper = document.createElement('div');
      childrenWrapper.className = 'tree-children';

      var childrenInner = document.createElement('div');
      childrenInner.className = 'tree-children-inner';
      item.children.forEach(function(child) {
        childrenInner.appendChild(createTreeItem(child));
      });

      childrenWrapper.appendChild(childrenInner);
      div.appendChild(childrenWrapper);
    }

    return div;
  }

  // ===========================================
  // Search
  // ===========================================

  function initSearch() {
    const searchInput = document.getElementById('file-search');
    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
      const query = this.value.toLowerCase().trim();
      const treeItems = document.querySelectorAll('.tree-item');

      treeItems.forEach(function(item) {
        const label = item.querySelector('.tree-label');
        if (label) {
          const text = label.textContent.toLowerCase();
          const matches = query === '' || text.includes(query);
          item.style.display = matches ? '' : 'none';
        }
      });
    });
  }

  // ===========================================
  // Sorting
  // ===========================================

  function initSorting() {
    const headers = document.querySelectorAll('.file-list-header .sortable, .functions-header .sortable');

    headers.forEach(function(header) {
      header.addEventListener('click', function() {
        const sortKey = this.dataset.sort;
        const isAscending = this.classList.contains('sorted-ascending');

        // Remove sorted class from all headers
        headers.forEach(function(h) {
          h.classList.remove('sorted-ascending', 'sorted-descending');
        });

        // Toggle sort direction
        this.classList.add(isAscending ? 'sorted-descending' : 'sorted-ascending');

        // Sort the list
        sortList(sortKey, !isAscending);
      });
    });
  }

  function sortList(key, ascending) {
    const container = document.getElementById('file-list') || document.querySelector('.functions-body');
    if (!container) return;

    const rows = Array.from(container.children);

    rows.sort(function(a, b) {
      let aVal = a.dataset[key] || a.querySelector('[data-sort]')?.dataset.sort || '';
      let bVal = b.dataset[key] || b.querySelector('[data-sort]')?.dataset.sort || '';

      // Try to parse as numbers
      const aNum = parseFloat(aVal);
      const bNum = parseFloat(bVal);

      if (!isNaN(aNum) && !isNaN(bNum)) {
        return ascending ? aNum - bNum : bNum - aNum;
      }

      // String comparison
      return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });

    rows.forEach(function(row) {
      container.appendChild(row);
    });
  }

  // ===========================================
  // Toggle Buttons (Coverage Lines)
  // ===========================================

  function initToggleButtons() {
    const buttons = document.querySelectorAll('.button_toggle_coveredLine, .button_toggle_uncoveredLine, .button_toggle_partialCoveredLine, .button_toggle_excludedLine');

    buttons.forEach(function(button) {
      button.addEventListener('click', function() {
        const lineClass = this.value;
        const showClass = 'show_' + lineClass;

        // Toggle the button state
        this.classList.toggle(showClass);

        // Toggle visibility of lines
        const lines = document.querySelectorAll('.' + lineClass);
        lines.forEach(function(line) {
          line.classList.toggle(showClass);
        });
      });
    });

    // Also handle simpler toggle buttons
    const simpleToggles = document.querySelectorAll('.btn-toggle');
    simpleToggles.forEach(function(button) {
      button.addEventListener('click', function() {
        const classes = Array.from(this.classList);
        const showClass = classes.find(function(c) { return c.startsWith('show_'); });

        if (showClass) {
          this.classList.toggle(showClass);
          const lineClass = showClass.replace('show_', '');
          const lines = document.querySelectorAll('.' + lineClass);
          lines.forEach(function(line) {
            line.classList.toggle(showClass);
          });
        }
      });
    });
  }

})();
