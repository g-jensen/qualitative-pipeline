local g = import 'github.com/grafana/grafonnet/gen/grafonnet-latest/main.libsonnet';

local datasourceName = 'tempo';
local serviceName = 'qualitative-pipeline';
local dashboardName = 'qualitative-pipeline';

// Haiku 4.5: $1.00 / $5.00 per million tokens
local inputPricePerToken = '0.000001';
local outputPricePerToken = '0.000005';

local groupByTransformation = {
  id: 'groupBy',
  options: {
    fields: {
      'Span ID': { aggregations: ['allValues'], operation: 'aggregate' },
      'Start time': { aggregations: ['first'], operation: 'aggregate' },
      input_tokens: { aggregations: ['sum'], operation: 'aggregate' },
      output_tokens: { aggregations: ['sum'], operation: 'aggregate' },
      traceIdHidden: { aggregations: ['sum'], operation: 'groupby' },
    },
  },
};

local sortByTime = {
  id: 'sortBy',
  options: { sort: [{ field: 'Start time (first)', desc: false }] },
};

local traceLink = {
  title: 'View trace',
  url: '/explore?left={"datasource":"' + datasourceName + '","queries":[{"query":"${__data.fields.traceIdHidden}","queryType":"traceql"}]}',
};

local calcBinary(left, op, right) = {
  id: 'calculateField',
  options: {
    mode: 'binary',
    binary: { left: left, operator: op, right: right },
    replaceFields: false,
  },
};

local calcBinaryAliased(alias, leftField, op, rightFixed) = {
  id: 'calculateField',
  options: {
    mode: 'binary',
    alias: alias,
    binary: {
      left: { matcher: { id: 'byName', options: leftField } },
      operator: op,
      right: { fixed: rightFixed },
    },
    reduce: { reducer: 'sum' },
    replaceFields: false,
  },
};

local calcBinaryFields(alias, leftField, rightField) = {
  id: 'calculateField',
  options: {
    mode: 'binary',
    alias: alias,
    binary: {
      left: { matcher: { id: 'byName', options: leftField } },
      right: { matcher: { id: 'byName', options: rightField } },
    },
    reduce: { reducer: 'sum' },
    replaceFields: false,
  },
};

local calcCumulative(alias, field) = {
  id: 'calculateField',
  options: {
    mode: 'cumulativeFunctions',
    alias: alias,
    cumulative: { field: field, reducer: 'sum' },
    reduce: { reducer: 'sum' },
  },
};

local filterFields(names) = {
  id: 'filterFieldsByName',
  options: {
    include: { names: names },
  },
};

local inputCostField = 'input_tokens (sum) * ' + inputPricePerToken;
local outputCostField = 'output_tokens (sum) * ' + outputPricePerToken;

local priceCalcSteps = [
  calcBinary('input_tokens (sum)', '*', inputPricePerToken),
  calcBinary('output_tokens (sum)', '*', outputPricePerToken),
  {
    id: 'organize',
    options: {
      renameByName: {
        [inputCostField]: 'input_cost',
        [outputCostField]: 'output_cost',
      },
    },
  },
  calcBinary('input_cost', '+', 'output_cost'),
];

local tempoQuery(query, refId='A') =
  g.query.tempo.new(datasourceName, query, [])
  + g.query.tempo.withQueryType('traceql')
  + g.query.tempo.withTableType('spans')
  + g.query.tempo.withLimit(20)
  + g.query.tempo.withRefId(refId);

local basePanel(title) =
  g.panel.timeSeries.new(title)
  + g.panel.timeSeries.options.legend.withDisplayMode('list')
  + g.panel.timeSeries.options.legend.withPlacement('bottom')
  + g.panel.timeSeries.options.legend.withShowLegend(true)
  + g.panel.timeSeries.options.tooltip.withMode('single')
  + g.panel.timeSeries.standardOptions.color.withMode('palette-classic')
  + g.panel.timeSeries.standardOptions.withLinks([traceLink])
  + g.panel.timeSeries.fieldConfig.defaults.custom.withLineWidth(1)
  + g.panel.timeSeries.fieldConfig.defaults.custom.withPointSize(9)
  + g.panel.timeSeries.fieldConfig.defaults.custom.withShowPoints('always')
  + g.panel.timeSeries.fieldConfig.defaults.custom.withSpanNulls(false);

local tokenPanel(title, query, barWidth=0.2) =
  basePanel(title)
  + g.panel.timeSeries.queryOptions.withTargets([tempoQuery(query)])
  + g.panel.timeSeries.queryOptions.withTransformations([groupByTransformation])
  + g.panel.timeSeries.fieldConfig.defaults.custom.withDrawStyle('bars')
  + g.panel.timeSeries.fieldConfig.defaults.custom.withFillOpacity(50)
  + g.panel.timeSeries.fieldConfig.defaults.custom.stacking.withMode('none')
  + { fieldConfig+: { defaults+: { custom+: {
    barWidthFactor: barWidth,
    showValues: true,
  } } } };

local pricePanel(title, query, barWidth=0.1) =
  tokenPanel(title, query, barWidth)
  + g.panel.timeSeries.standardOptions.withUnit('currencyUSD')
  + g.panel.timeSeries.standardOptions.withDecimals(4)
  + g.panel.timeSeries.queryOptions.withTransformations(
    [groupByTransformation, sortByTime] + priceCalcSteps + [{
      id: 'organize',
      options: {
        excludeByName: {
          'input_tokens (sum)': true,
          'output_tokens (sum)': true,
          'Span ID (allValues)': true,
        },
      },
    }]
  );

local cumulativePricePanel(title, query) =
  basePanel(title)
  + g.panel.timeSeries.queryOptions.withTargets([tempoQuery(query)])
  + g.panel.timeSeries.queryOptions.withTransformations([
    groupByTransformation,
    sortByTime,
    calcBinaryAliased('input_cost', 'input_tokens (sum)', '*', inputPricePerToken),
    calcBinaryAliased('output_cost', 'output_tokens (sum)', '*', outputPricePerToken),
    filterFields(['traceIdHidden', 'Span ID (allValues)', 'Start time (first)', 'input_cost', 'output_cost']),
    calcCumulative('cum_input_cost', 'input_cost'),
    calcCumulative('cum_output_cost', 'output_cost'),
    calcBinaryFields('cum_total_cost', 'cum_input_cost', 'cum_output_cost'),
    filterFields(['traceIdHidden', 'Span ID (allValues)', 'Start time (first)', 'cum_input_cost', 'cum_output_cost', 'cum_total_cost']),
  ])
  + g.panel.timeSeries.standardOptions.withUnit('currencyUSD')
  + g.panel.timeSeries.standardOptions.withDecimals(4)
  + g.panel.timeSeries.fieldConfig.defaults.custom.withDrawStyle('line')
  + g.panel.timeSeries.fieldConfig.defaults.custom.withFillOpacity(0)
  + g.panel.timeSeries.fieldConfig.defaults.custom.withLineWidth(2);

local allTokensQuery =
  '{ resource.service.name = "' + serviceName + '" && name = "reframeQuote" }'
  + ' > { span.input_tokens != nil && span.output_tokens != nil }';

local claudeTokensQuery =
  '{ resource.service.name = "' + serviceName + '" && span.model =~ "claude.*" }'
  + ' >> { span.input_tokens != nil && span.output_tokens != nil }';

g.dashboard.new(dashboardName)
+ g.dashboard.withTimezone('browser')
+ g.dashboard.time.withFrom('now-6h')
+ g.dashboard.time.withTo('now')
+ g.dashboard.withPanels(
  g.util.grid.makeGrid([
    tokenPanel('All Tokens', allTokensQuery, barWidth=0.2),
    g.panel.row.new('Claude')
    + g.panel.row.withPanels([
      tokenPanel('Claude Tokens', claudeTokensQuery, barWidth=0.1),
      pricePanel('Claude Cost', claudeTokensQuery, barWidth=0.1),
      cumulativePricePanel('Claude Cumulative Cost', claudeTokensQuery),
    ])
  ], panelWidth=12, panelHeight=8)
)
