/**
 * A股-美股映射分析服务
 *
 * 功能：
 *   1. 构建A股-美股映射矩阵
 *   2. 分析海外评级变动对A股的影响
 *   3. 生成影响分析报告
 *
 * 小白讲解：
 *   这个服务就像一个"跨境情报分析员"，它能：
 *   - 看懂海外评级变动的含义（比如NVDA被调高评级意味着什么）
 *   - 找到影响传导路径（NVDA评级上调 → A股光模块需求增加）
 *   - 给出A股投资建议（应该关注哪些A股标的）
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { WallstreetDataService } from './wallstreet-data-service.js';
import { createChatCompletion } from './llm-service.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * 映射分析服务类
 */
export class MappingAnalysisService {
  constructor() {
    this.wallstreetService = new WallstreetDataService();
    this.loadConfig();
  }

  /**
   * 加载行业映射配置
   */
  loadConfig() {
    const configPath = join(__dirname, '../config/sector_mapping_config.json');
    try {
      const configContent = readFileSync(configPath, 'utf-8');
      this.config = JSON.parse(configContent);
      console.log(`[mapping] 加载行业映射配置：${this.config.sectors.length}个行业`);
    } catch (e) {
      console.error('[mapping] 加载配置失败:', e.message);
      this.config = { sectors: [], mappingTypes: {} };
    }
  }

  /**
   * 获取所有行业配置
   */
  getAllSectors() {
    return this.config.sectors || [];
  }

  /**
   * 根据行业Key获取行业配置
   */
  getSectorByKey(sectorKey) {
    return this.config.sectors.find(s => s.sectorKey === sectorKey);
  }

  /**
   * 根据A股标的查找相关行业配置
   */
  findSectorByTarget(targetTicker) {
    const codeOnly = targetTicker.replace(/\.(SZ|SH|BJ|HK)$/i, '');
    return this.config.sectors.find(s => 
      s.coreTargets.some(t => t.replace(/\.(SZ|SH|BJ|HK)$/i, '') === codeOnly)
    );
  }

  /**
   * 构建完整的映射矩阵
   *
   * 返回：
   *   包含所有行业、美股对标、A股标的的映射矩阵
   */
  buildMappingMatrix() {
    const matrix = [];
    
    for (const sector of this.config.sectors) {
      matrix.push({
        sectorKey: sector.sectorKey,
        sectorName: sector.sectorName,
        usBenchmarks: sector.usBenchmarks,
        mappingType: sector.mappingType,
        mappingTypeName: this.config.mappingTypes[sector.mappingType]?.name || sector.mappingType,
        aShareSectors: sector.aShareSectors,
        coreTargets: sector.coreTargets,
        impactLevel: sector.impactLevel,
        correlation: sector.correlation,
        description: sector.description,
        mappingDescription: sector.mappingDescription,
      });
    }
    
    return matrix;
  }

  /**
   * 分析海外评级变动对A股的影响
   *
   * 参数：
   *   sectorKey: 行业Key（可选，如果不传则分析所有行业）
   *   forceUpdate: 是否强制更新数据（默认false，使用缓存）
   *
   * 返回：
   *   影响分析结果，包含每个美股标的的评级变动和对应的A股影响
   */
  async analyzeImpact(sectorKey = null, forceUpdate = false) {
    console.log(`[mapping] 开始分析海外评级变动影响${sectorKey ? `（行业：${sectorKey}）` : ''}`);

    const sectors = sectorKey 
      ? this.config.sectors.filter(s => s.sectorKey === sectorKey)
      : this.config.sectors;

    const results = [];

    for (const sector of sectors) {
      console.log(`[mapping] 分析行业：${sector.sectorName}`);
      
      const sectorImpact = {
        sectorKey: sector.sectorKey,
        sectorName: sector.sectorName,
        mappingType: sector.mappingType,
        mappingDescription: sector.mappingDescription,
        impactLevel: sector.impactLevel,
        correlation: sector.correlation,
        usBenchmarks: [],
        aShareImpact: [],
        overallSignal: 'neutral',
        overallConfidence: 0,
      };

      // 获取每个美股对标公司的评级数据
      for (const symbol of sector.usBenchmarks) {
        const wsData = await this.wallstreetService.getAllWallstreetData(symbol);
        
        if (Object.keys(wsData.ratings).length > 0) {
          const rating = wsData.ratings;
          
          // 判断评级信号
          const signal = this._judgeRatingSignal(rating);
          
          sectorImpact.usBenchmarks.push({
            symbol,
            source: rating.source,
            totalAnalysts: rating.totalAnalysts || 0,
            buy: rating.buy || 0,
            hold: rating.hold || 0,
            sell: rating.sell || 0,
            buyRatio: parseFloat(rating.buyRatio) || 0,
            sellRatio: parseFloat(rating.sellRatio) || 0,
            targetMeanPrice: rating.targetMeanPrice,
            currentPrice: rating.currentPrice,
            upside: rating.upside ? parseFloat(rating.upside) : null,
            signal,
            news: wsData.news.slice(0, 3).map(n => ({
              date: n.date,
              headline: n.headline,
              source: n.source,
            })),
          });
        }
      }

      // 综合判断行业影响
      sectorImpact.overallSignal = this._calculateOverallSignal(sectorImpact.usBenchmarks);
      sectorImpact.overallConfidence = this._calculateConfidence(sectorImpact.usBenchmarks);

      // 生成A股影响建议
      sectorImpact.aShareImpact = this._generateAShareImpact(sector, sectorImpact.usBenchmarks);

      results.push(sectorImpact);
    }

    return results;
  }

  /**
   * 根据评级数据判断信号
   */
  _judgeRatingSignal(rating) {
    const buyRatio = parseFloat(rating.buyRatio) || 0;
    const sellRatio = parseFloat(rating.sellRatio) || 0;
    
    if (buyRatio >= 70) return 'bullish';
    if (buyRatio >= 50 && sellRatio < 10) return 'slightly_bullish';
    if (sellRatio >= 20) return 'bearish';
    if (sellRatio >= 10 && buyRatio < 50) return 'slightly_bearish';
    return 'neutral';
  }

  /**
   * 计算综合信号
   */
  _calculateOverallSignal(benchmarks) {
    if (benchmarks.length === 0) return 'neutral';
    
    const bullishCount = benchmarks.filter(b => b.signal === 'bullish' || b.signal === 'slightly_bullish').length;
    const bearishCount = benchmarks.filter(b => b.signal === 'bearish' || b.signal === 'slightly_bearish').length;
    
    if (bullishCount >= benchmarks.length * 0.7) return 'bullish';
    if (bullishCount > bearishCount) return 'slightly_bullish';
    if (bearishCount >= benchmarks.length * 0.7) return 'bearish';
    if (bearishCount > bullishCount) return 'slightly_bearish';
    return 'neutral';
  }

  /**
   * 计算置信度
   */
  _calculateConfidence(benchmarks) {
    if (benchmarks.length === 0) return 0;
    
    let totalWeight = 0;
    let confidenceSum = 0;
    
    for (const b of benchmarks) {
      const weight = b.totalAnalysts || 1;
      totalWeight += weight;
      
      let confidence = 50; // 基础置信度
      if (b.signal === 'bullish') confidence += 30;
      if (b.signal === 'bearish') confidence += 30;
      if (b.signal === 'slightly_bullish') confidence += 15;
      if (b.signal === 'slightly_bearish') confidence += 15;
      if (b.totalAnalysts >= 30) confidence += 10;
      if (b.totalAnalysts >= 50) confidence += 10;
      
      confidenceSum += confidence * weight;
    }
    
    return Math.round(confidenceSum / totalWeight);
  }

  /**
   * 生成A股影响建议
   */
  _generateAShareImpact(sector, benchmarks) {
    const impacts = [];
    const mappingType = this.config.mappingTypes[sector.mappingType];
    
    for (const target of sector.coreTargets) {
      let impactDirection = 'neutral';
      let impactLevel = 'low';
      let reasoning = '';
      
      // 根据映射类型和海外信号生成影响分析
      if (benchmarks.length > 0) {
        const overallSignal = this._calculateOverallSignal(benchmarks);
        
        if (overallSignal === 'bullish' || overallSignal === 'slightly_bullish') {
          impactDirection = 'positive';
          impactLevel = sector.impactLevel;
          reasoning = `${mappingType?.impactPattern || '海外评级正面'}，${sector.sectorName}板块受益`;
        } else if (overallSignal === 'bearish' || overallSignal === 'slightly_bearish') {
          impactDirection = 'negative';
          impactLevel = sector.impactLevel;
          reasoning = `${mappingType?.impactPattern || '海外评级负面'}，${sector.sectorName}板块承压`;
        } else {
          reasoning = '海外评级中性，暂无明确影响';
        }
      } else {
        reasoning = '暂无海外评级数据';
      }
      
      impacts.push({
        ticker: target,
        impactDirection,
        impactLevel,
        reasoning,
        correlation: sector.correlation,
      });
    }
    
    return impacts;
  }

  /**
   * 生成完整的影响分析报告（文本格式，用于LLM或直接展示）
   *
   * 参数：
   *   analysisResults: analyzeImpact返回的结果
   *
   * 返回：
   *   格式化的报告文本
   */
  generateImpactReport(analysisResults) {
    if (!analysisResults || analysisResults.length === 0) {
      return "暂无海外评级影响分析数据";
    }

    let report = `# 🌍 A股-美股映射影响分析报告\n\n`;
    report += `**生成时间**: ${new Date().toLocaleString('zh-CN')}\n\n`;
    report += `---\n\n`;

    // 汇总摘要
    let bullishCount = 0;
    let bearishCount = 0;
    let neutralCount = 0;
    
    for (const sector of analysisResults) {
      if (sector.overallSignal === 'bullish' || sector.overallSignal === 'slightly_bullish') bullishCount++;
      else if (sector.overallSignal === 'bearish' || sector.overallSignal === 'slightly_bearish') bearishCount++;
      else neutralCount++;
    }

    report += `## 📊 整体摘要\n`;
    report += `| 信号类型 | 行业数量 |\n`;
    report += `|---|---|\n`;
    report += `| 🟢 看多 | ${bullishCount} |\n`;
    report += `| 🔴 看空 | ${bearishCount} |\n`;
    report += `| ⚪ 中性 | ${neutralCount} |\n\n`;

    // 详细分析
    for (const sector of analysisResults) {
      report += `## ${this._getSignalEmoji(sector.overallSignal)} ${sector.sectorName}\n\n`;
      report += `**映射类型**: ${this.config.mappingTypes[sector.mappingType]?.name || sector.mappingType}\n`;
      report += `**映射描述**: ${sector.mappingDescription}\n`;
      report += `**影响级别**: ${this._getImpactLevelEmoji(sector.impactLevel)} ${sector.impactLevel}\n`;
      report += `**相关性**: ${(sector.correlation * 100).toFixed(0)}%\n`;
      report += `**综合信号**: ${this._getSignalText(sector.overallSignal)}（置信度${sector.overallConfidence}%）\n\n`;

      // 美股对标评级
      report += `### 🇺🇸 海外对标评级\n`;
      report += `| 标的 | 分析师数 | Buy | Hold | Sell | Buy% | 信号 |\n`;
      report += `|---|---|---|---|---|---|---|\n`;
      for (const b of sector.usBenchmarks) {
        report += `| ${b.symbol} | ${b.totalAnalysts} | ${b.buy} | ${b.hold} | ${b.sell} | ${b.buyRatio}% | ${this._getSignalEmoji(b.signal)} |\n`;
      }
      report += `\n`;

      // A股影响
      report += `### 📈 A股影响建议\n`;
      report += `| A股标的 | 影响方向 | 影响级别 | 相关性 | 理由 |\n`;
      report += `|---|---|---|---|---|\n`;
      for (const impact of sector.aShareImpact) {
        report += `| ${impact.ticker} | ${this._getDirectionEmoji(impact.impactDirection)} | ${impact.impactLevel} | ${(impact.correlation * 100).toFixed(0)}% | ${impact.reasoning} |\n`;
      }
      report += `\n---\n\n`;
    }

    return report;
  }

  _getSignalEmoji(signal) {
    switch (signal) {
      case 'bullish': return '🟢';
      case 'slightly_bullish': return '🟡';
      case 'bearish': return '🔴';
      case 'slightly_bearish': return '🟠';
      default: return '⚪';
    }
  }

  _getSignalText(signal) {
    switch (signal) {
      case 'bullish': return '强烈看多';
      case 'slightly_bullish': return '小幅看多';
      case 'bearish': return '强烈看空';
      case 'slightly_bearish': return '小幅看空';
      default: return '中性';
    }
  }

  _getImpactLevelEmoji(level) {
    switch (level) {
      case 'high': return '🚨';
      case 'medium': return '⚠️';
      case 'low': return 'ℹ️';
      default: return 'ℹ️';
    }
  }

  _getDirectionEmoji(direction) {
    switch (direction) {
      case 'positive': return '⬆️';
      case 'negative': return '⬇️';
      default: return '➡️';
    }
  }

  /**
   * 针对单个A股标的的海外影响分析
   *
   * 参数：
   *   targetTicker: A股标的代码
   *
   * 返回：
   *   该标的的海外影响分析
   */
  async analyzeTargetImpact(targetTicker) {
    const sector = this.findSectorByTarget(targetTicker);
    if (!sector) {
      return {
        success: false,
        message: `未找到 ${targetTicker} 的行业配置`,
      };
    }

    const results = await this.analyzeImpact(sector.sectorKey);
    if (results.length === 0) {
      return {
        success: false,
        message: '未能获取海外评级数据',
      };
    }

    const sectorResult = results[0];
    const targetImpact = sectorResult.aShareImpact.find(
      i => i.ticker === targetTicker
    );

    return {
      success: true,
      ticker: targetTicker,
      sector: sector,
      overallSignal: sectorResult.overallSignal,
      overallConfidence: sectorResult.overallConfidence,
      targetImpact,
      usBenchmarks: sectorResult.usBenchmarks,
      report: this.generateImpactReport(results),
    };
  }

  /**
   * 运行完整的海外映射分析工作流
   */
  async runMappingAnalysis() {
    console.log('[mapping] 开始运行海外映射分析工作流');
    
    const results = await this.analyzeImpact();
    const report = this.generateImpactReport(results);
    
    console.log('[mapping] 海外映射分析完成');
    return {
      success: true,
      analysisResults: results,
      report,
      sectorCount: results.length,
    };
  }

  /**
   * 统一映射查找入口（三层查找）
   *
   * 查找顺序：
   *   1. 第一层：专家配置映射（精度最高，速度最快）
   *   2. 第二层：行业分类映射（覆盖所有A股标的）
   *   3. 第三层：LLM语义映射（处理偶发关联）
   *
   * 参数：
   *   usTicker: 美股代码（如 NVDA）
   *   catalyst: 异动原因（可选，用于提高映射精度）
   *   userQuery: 用户查询（可选，用于LLM语义匹配）
   *
   * 返回：
   *   映射结果对象，包含映射标的、维度、强度等
   */
  async findMapping(usTicker, catalyst = null, userQuery = null) {
    console.log(`[mapping] 开始查找 ${usTicker} 的映射关系`);

    // 第一层：专家配置映射
    const configMapping = await this.findMappingByConfig(usTicker);
    if (configMapping && configMapping.aShareTargets.length > 0) {
      console.log(`[mapping] ✅ 在配置中找到映射`);
      return configMapping;
    }

    // 第二层：行业分类映射
    const sectorMapping = await this.findMappingBySector(usTicker, catalyst);
    if (sectorMapping && sectorMapping.aShareTargets.length > 0) {
      console.log(`[mapping] ✅ 通过行业分类找到映射`);
      return sectorMapping;
    }

    // 第三层：LLM语义映射
    const llmMapping = await this.findMappingByLLM(usTicker, catalyst, userQuery);
    if (llmMapping && llmMapping.aShareTargets.length > 0) {
      console.log(`[mapping] ✅ 通过LLM语义匹配找到映射`);
      return llmMapping;
    }

    // 都没找到，返回默认结果
    console.log(`[mapping] ⚠️ 未找到 ${usTicker} 的映射关系`);
    return {
      usTicker,
      found: false,
      mappingLevel: 'none',
      aShareTargets: [],
      mappingType: 'unknown',
      mappingStrength: 0,
      reasoning: `未找到 ${usTicker} 的A股映射关系`,
    };
  }

  /**
   * 第一层：从配置文件查找映射（已有逻辑封装）
   */
  async findMappingByConfig(usTicker) {
    const symbol = usTicker.toUpperCase();
    
    for (const sector of this.config.sectors) {
      if (sector.usBenchmarks.includes(symbol)) {
        const wsData = await this.wallstreetService.getAllWallstreetData(symbol);
        const rating = wsData.ratings;
        const signal = Object.keys(rating).length > 0 ? this._judgeRatingSignal(rating) : 'neutral';
        
        return {
          usTicker: symbol,
          found: true,
          mappingLevel: 'config',
          sectorKey: sector.sectorKey,
          sectorName: sector.sectorName,
          aShareTargets: sector.coreTargets,
          mappingType: sector.mappingType,
          mappingTypeName: this.config.mappingTypes[sector.mappingType]?.name || sector.mappingType,
          mappingStrength: sector.correlation,
          reasoning: `专家配置：${sector.mappingDescription}`,
          benchmarkSignal: signal,
          correlation: sector.correlation,
          impactLevel: sector.impactLevel,
        };
      }
    }
    
    return null;
  }

  /**
   * 第二层：基于行业分类的动态映射
   *
   * 通过分析美股行业，自动匹配A股同行业标的
   */
  async findMappingBySector(usTicker, catalyst = null) {
    const symbol = usTicker.toUpperCase();
    
    const sectorMap = {
      'NVDA': '半导体/芯片',
      'AMD': '半导体/芯片',
      'INTC': '半导体/芯片',
      'AVGO': '半导体/芯片',
      'QCOM': '半导体/芯片',
      'MU': '半导体/芯片',
      'MSFT': '软件/云计算',
      'GOOGL': '互联网/云计算',
      'AAPL': '消费电子',
      'META': '互联网/社交',
      'AMZN': '电商/云计算',
      'TSLA': '新能源车',
      'NIO': '新能源车',
      'XPEV': '新能源车',
      'RIVN': '新能源车',
      'ISRG': '医疗器械',
      'JNJ': '医药',
      'PFE': '医药',
      'MRK': '医药',
      'LITE': '光模块',
      'MRVL': '半导体',
      'SWKS': '半导体',
      'FTNT': '网络安全',
      'SNOW': '云计算',
      'CRM': '软件',
      'ORCL': '软件/数据库',
      'PLTR': '软件',
      'PATH': '软件',
      'ROKU': '流媒体',
      'CRWD': '网络安全',
      'ENPH': '新能源',
      'PLUG': '新能源',
    };

    const aShareSectorMap = {
      '半导体/芯片': [
        { ticker: '688041.SH', name: '海光信息', correlation: 0.85 },
        { ticker: '688256.SH', name: '寒武纪', correlation: 0.82 },
        { ticker: '002371.SZ', name: '北方华创', correlation: 0.78 },
        { ticker: '300671.SZ', name: '圣邦股份', correlation: 0.75 },
        { ticker: '688008.SH', name: '澜起科技', correlation: 0.72 },
        { ticker: '00981.HK', name: '中芯国际', correlation: 0.80 },
        { ticker: '688521.SH', name: '芯原股份', correlation: 0.70 },
        { ticker: '688525.SH', name: '芯海科技', correlation: 0.65 },
      ],
      '光模块': [
        { ticker: '300308.SZ', name: '中际旭创', correlation: 0.82 },
        { ticker: '300502.SZ', name: '新易盛', correlation: 0.78 },
        { ticker: '300394.SZ', name: '天孚通信', correlation: 0.75 },
        { ticker: '002281.SZ', name: '光迅科技', correlation: 0.72 },
        { ticker: '603083.SH', name: '剑桥科技', correlation: 0.70 },
      ],
      '新能源车': [
        { ticker: '300750.SZ', name: '宁德时代', correlation: 0.75 },
        { ticker: '002594.SZ', name: '比亚迪', correlation: 0.72 },
        { ticker: '300014.SZ', name: '亿纬锂能', correlation: 0.68 },
        { ticker: '300274.SZ', name: '阳光电源', correlation: 0.65 },
        { ticker: '601012.SH', name: '隆基绿能', correlation: 0.60 },
      ],
      '软件/云计算': [
        { ticker: '688111.SH', name: '金山办公', correlation: 0.65 },
        { ticker: '002230.SZ', name: '科大讯飞', correlation: 0.62 },
        { ticker: '600588.SH', name: '用友网络', correlation: 0.58 },
        { ticker: '300454.SZ', name: '深信服', correlation: 0.55 },
        { ticker: '600845.SH', name: '宝信软件', correlation: 0.52 },
      ],
      '互联网/云计算': [
        { ticker: '09988.HK', name: '阿里巴巴', correlation: 0.60 },
        { ticker: '09980.HK', name: '网易', correlation: 0.55 },
        { ticker: '03690.HK', name: '美团', correlation: 0.58 },
        { ticker: '01810.HK', name: '小米集团', correlation: 0.52 },
      ],
      '消费电子': [
        { ticker: '000063.SZ', name: '中兴通讯', correlation: 0.70 },
        { ticker: '002475.SZ', name: '立讯精密', correlation: 0.65 },
        { ticker: '601231.SH', name: '环旭电子', correlation: 0.60 },
        { ticker: '300124.SZ', name: '汇川技术', correlation: 0.68 },
      ],
      '医药': [
        { ticker: '600276.SH', name: '恒瑞医药', correlation: 0.68 },
        { ticker: '603259.SH', name: '药明康德', correlation: 0.72 },
        { ticker: '300760.SZ', name: '迈瑞医疗', correlation: 0.70 },
        { ticker: '300122.SZ', name: '智飞生物', correlation: 0.60 },
      ],
      '医疗器械': [
        { ticker: '300760.SZ', name: '迈瑞医疗', correlation: 0.75 },
        { ticker: '688677.SH', name: '海泰新光', correlation: 0.65 },
        { ticker: '688030.SH', name: '威高骨科', correlation: 0.60 },
      ],
      '互联网/社交': [
        { ticker: '00700.HK', name: '腾讯控股', correlation: 0.65 },
        { ticker: '03690.HK', name: '美团', correlation: 0.60 },
        { ticker: '09988.HK', name: '阿里巴巴', correlation: 0.58 },
      ],
      '电商/云计算': [
        { ticker: '09988.HK', name: '阿里巴巴', correlation: 0.62 },
        { ticker: '03690.HK', name: '美团', correlation: 0.58 },
        { ticker: '01810.HK', name: '京东集团', correlation: 0.55 },
      ],
      '网络安全': [
        { ticker: '300454.SZ', name: '深信服', correlation: 0.65 },
        { ticker: '002439.SZ', name: '启明星辰', correlation: 0.60 },
        { ticker: '688023.SH', name: '安恒信息', correlation: 0.58 },
      ],
      '流媒体': [
        { ticker: '09999.HK', name: '哔哩哔哩', correlation: 0.55 },
        { ticker: '09888.HK', name: '百度集团', correlation: 0.50 },
      ],
      '新能源': [
        { ticker: '300750.SZ', name: '宁德时代', correlation: 0.70 },
        { ticker: '601012.SH', name: '隆基绿能', correlation: 0.65 },
        { ticker: '300274.SZ', name: '阳光电源', correlation: 0.62 },
      ],
    };

    const sector = sectorMap[symbol];
    if (!sector) {
      return null;
    }

    const aShareTargets = aShareSectorMap[sector];
    if (!aShareTargets) {
      return null;
    }

    // 根据催化剂调整映射类型和强度
    let mappingType = 'valuation';
    let mappingStrength = 0.6;
    let reasoning = `行业分类映射：${usTicker}属于${sector}行业，A股同行业标的受益`;

    if (catalyst) {
      if (catalyst.includes('业绩') || catalyst.includes('财报') || catalyst.includes('收入')) {
        mappingType = 'demand';
        mappingStrength = Math.min(0.8, mappingStrength + 0.15);
        reasoning = `${reasoning}。${usTicker}业绩超预期，需求端受益`;
      } else if (catalyst.includes('评级') || catalyst.includes('目标价')) {
        mappingType = 'valuation';
        mappingStrength = Math.min(0.75, mappingStrength + 0.1);
        reasoning = `${reasoning}。${usTicker}评级上调，估值锚定效应`;
      } else if (catalyst.includes('订单') || catalyst.includes('客户')) {
        mappingType = 'supply';
        mappingStrength = Math.min(0.85, mappingStrength + 0.2);
        reasoning = `${reasoning}。${usTicker}订单增加，供应链受益`;
      } else if (catalyst.includes('技术') || catalyst.includes('产品')) {
        mappingType = 'technology';
        mappingStrength = Math.min(0.75, mappingStrength + 0.15);
        reasoning = `${reasoning}。${usTicker}技术突破，技术路线跟随`;
      }
    }

    return {
      usTicker: symbol,
      found: true,
      mappingLevel: 'sector',
      sector,
      aShareTargets: aShareTargets.map(t => t.ticker),
      aShareTargetsWithInfo: aShareTargets,
      mappingType,
      mappingTypeName: this.config.mappingTypes[mappingType]?.name || mappingType,
      mappingStrength,
      reasoning,
      correlation: mappingStrength,
      impactLevel: mappingStrength > 0.75 ? 'high' : mappingStrength > 0.65 ? 'medium' : 'low',
    };
  }

  /**
   * 第三层：LLM语义映射
   *
   * 使用LLM分析用户查询和上下文，发现潜在的映射关系
   */
  async findMappingByLLM(usTicker, catalyst = null, userQuery = null) {
    const prompt = `
你是一个专业的投研助手，负责分析美股和A股之间的映射关系。

## 分析任务
美股标的：${usTicker}
异动原因：${catalyst || '无'}
用户查询：${userQuery || '无'}

## 请分析：
1. 该美股属于什么行业？
2. A股有哪些相关标的？（列出5-10个）
3. 映射维度是什么？（supply=供应链, demand=需求, technology=技术路线, valuation=估值锚定）
4. 映射强度如何？（0-1之间）
5. 为什么这样映射？

## 输出格式（纯JSON）
{
  "sector": "行业名称",
  "aShareTargets": [
    {"ticker": "A股代码", "name": "公司名称", "correlation": 相关性}
  ],
  "mappingType": "映射维度",
  "mappingStrength": 映射强度,
  "reasoning": "映射理由"
}
`;

    try {
      const result = await createChatCompletion(prompt);
      const jsonStr = this._extractJSON(result);
      const parsed = JSON.parse(jsonStr);

      return {
        usTicker,
        found: true,
        mappingLevel: 'llm',
        sector: parsed.sector,
        aShareTargets: parsed.aShareTargets?.map(t => t.ticker) || [],
        aShareTargetsWithInfo: parsed.aShareTargets || [],
        mappingType: parsed.mappingType || 'valuation',
        mappingTypeName: this.config.mappingTypes[parsed.mappingType]?.name || parsed.mappingType,
        mappingStrength: parsed.mappingStrength || 0.5,
        reasoning: parsed.reasoning || `LLM分析：${usTicker}与A股相关标的存在映射关系`,
        correlation: parsed.mappingStrength || 0.5,
        impactLevel: parsed.mappingStrength > 0.75 ? 'high' : parsed.mappingStrength > 0.65 ? 'medium' : 'low',
      };
    } catch (error) {
      console.error('[mapping] LLM映射分析失败:', error.message);
      return null;
    }
  }

  /**
   * 从文本中提取JSON
   */
  _extractJSON(text) {
    const match = text.match(/\{[\s\S]*\}/);
    return match ? match[0] : text;
  }

  /**
   * 根据映射结果分析对A股的影响
   */
  async analyzeImpactFromMapping(mappingResult, usAnalysis = null) {
    if (!mappingResult.found) {
      return {
        success: false,
        message: `未找到 ${mappingResult.usTicker} 的映射关系`,
      };
    }

    const impactResults = [];
    const signal = usAnalysis?.signal || 'neutral';
    const overallSignal = signal === 'bullish' || signal === 'slightly_bullish' ? 'positive' :
                          signal === 'bearish' || signal === 'slightly_bearish' ? 'negative' : 'neutral';

    for (const target of mappingResult.aShareTargetsWithInfo || 
         mappingResult.aShareTargets.map(t => ({ ticker: t, correlation: mappingResult.correlation }))) {
      impactResults.push({
        ticker: target.ticker,
        name: target.name || '',
        impactDirection: overallSignal,
        impactLevel: mappingResult.impactLevel,
        correlation: target.correlation || mappingResult.correlation,
        reasoning: mappingResult.reasoning,
        mappingType: mappingResult.mappingType,
        mappingTypeName: mappingResult.mappingTypeName,
      });
    }

    return {
      success: true,
      usTicker: mappingResult.usTicker,
      mappingLevel: mappingResult.mappingLevel,
      mappingType: mappingResult.mappingType,
      mappingTypeName: mappingResult.mappingTypeName,
      mappingStrength: mappingResult.mappingStrength,
      overallSignal: overallSignal,
      reasoning: mappingResult.reasoning,
      aShareImpact: impactResults,
      sector: mappingResult.sector || mappingResult.sectorName,
    };
  }
}