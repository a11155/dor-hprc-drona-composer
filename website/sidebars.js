/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    {
      type: 'category',
      label: 'User Guide',
      items: [
        'user-guide/using-drona',
        'user-guide/primers',
      ],
    },
    {
      type: 'category',
      label: 'Overview',
      items: [
        'overview/intro',
        'overview/architecture',
        'overview/getting-started',
        'overview/installation',
      ],
    },
    {
      type: 'category',
      label: 'Frontend',
      items: [
        'frontend/overview',
        'frontend/form-components',
      ],
    },
    {
      type: 'category',
      label: 'Environment Development',
      items: [
        'environments/overview',
        'environments/schema',
        'environments/map',
        'environments/user-workflows',
        'environments/publishing',
	'environments/retriever-scripts',
	'environments/database'
      ],
    },
    'citations',
  ],
};

module.exports = sidebars;
