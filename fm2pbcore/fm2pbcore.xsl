<?xml version="1.0"?>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="http://www.pbcore.org/PBCore/PBCoreNamespace.html"
  xmlns:p="http://www.pbcore.org/PBCore/PBCoreNamespace.html"
  xmlns:f="http://www.filemaker.com/xml/fmresultset"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:str="http://exslt.org/strings"
  version="1.0"
  extension-element-prefixes="f xsi str p">
  <xsl:output encoding="UTF-8" method="xml" version="1.0" indent="yes"/>
  <xsl:template match="/f:fmresultset/f:resultset">
    <pbcoreCollection>
      <xsl:apply-templates select="f:record"/>
    </pbcoreCollection>
  </xsl:template>
  <xsl:template match="f:record">
    <pbcoreDescriptionDocument>
      <xsl:for-each select="f:relatedset[@table='PBCoreAssetType']/f:record">
        <pbcoreAssetType>
          <xsl:value-of select="f:field[@name='PBCoreAssetType::assetType']/f:data"/>
        </pbcoreAssetType>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreDate']/f:record">
        <pbcoreAssetDate>
          <xsl:if test="f:field[@name='PBCoreDate::dateType']/f:data">
            <xsl:attribute name="dateType">
              <xsl:value-of select="f:field[@name='PBCoreDate::dateType']/f:data"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:value-of select="f:field[@name='PBCoreDate::datevalue']/f:data"/>
        </pbcoreAssetDate>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreIdentifier']/f:record">
        <pbcoreIdentifier>
          <xsl:if test="f:field[@name='PBCoreIdentifier::identifierSource']/f:data">
            <xsl:attribute name="source">
              <xsl:value-of select="f:field[@name='PBCoreIdentifier::identifierSource']/f:data"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:value-of select="f:field[@name='PBCoreIdentifier::identifier']/f:data"/>
        </pbcoreIdentifier>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreTitle']/f:record">
        <pbcoreTitle>
          <xsl:if test="f:field[@name='PBCoreTitle::titleType']/f:data">
            <xsl:attribute name="titleType">
              <xsl:value-of select="f:field[@name='PBCoreTitle::titleType']/f:data"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:value-of select="f:field[@name='PBCoreTitle::title']/f:data"/>
        </pbcoreTitle>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreSubject']/f:record">
        <pbcoreSubject>
          <xsl:if test="f:field[@name='PBCoreSubject::subjectAuthorityUsed']/f:data">
            <xsl:attribute name="subjectAuthorityUsed">
              <xsl:value-of select="f:field[@name='PBCoreSubject::subjectAuthorityUsed']/f:data"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:value-of select="f:field[@name='PBCoreSubject::subject']/f:data"/>
        </pbcoreSubject>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreDescription']/f:record">
        <pbcoreDescription>
          <xsl:if test="f:field[@name='PBCoreDescription::descriptionType']/f:data">
            <xsl:attribute name="descriptionType">
              <xsl:value-of select="f:field[@name='PBCoreDescription::descriptionType']/f:data"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:value-of select="f:field[@name='PBCoreDescription::description']/f:data"/>
        </pbcoreDescription>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreGenre']/f:record">
        <pbcoreGenre>
          <xsl:if test="f:field[@name='PBCoreGenre::genreAuthorityUsed']/f:data">
            <xsl:attribute name="genreAuthorityUsed">
              <xsl:value-of select="f:field[@name='PBCoreGenre::genreAuthorityUsed']/f:data"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:value-of select="f:field[@name='PBCoreGenre::genre']/f:data"/>
        </pbcoreGenre>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreRelation']/f:record">
        <pbcoreRelation>
          <xsl:if test="f:field[@name='PBCoreRelation::relationType']/f:data">
            <pbcoreRelationType>
              <xsl:value-of select="f:field[@name='PBCoreRelation::relationType']/f:data"/>
            </pbcoreRelationType>
          </xsl:if>
          <xsl:if test="f:field[@name='PBCoreRelation::relationIdentifier']/f:data">
            <pbcoreRelationIdentifier>
              <xsl:value-of select="f:field[@name='PBCoreRelation::relationIdentifier']/f:data"/>
            </pbcoreRelationIdentifier>
          </xsl:if>
        </pbcoreRelation>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreCreator']/f:record">
        <pbcoreCreator>
          <creator>
            <xsl:value-of select="f:field[@name='PBCoreCreator::creator']/f:data"/>
          </creator>
          <xsl:for-each select="f:field[@name='PBCoreRole_Creator::role']/f:data">
            <creatorRole>
              <xsl:value-of select="."/>
            </creatorRole>
          </xsl:for-each>
        </pbcoreCreator>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCoreContributor']/f:record">
        <pbcoreContributor>
          <contributor>
            <xsl:value-of select="f:field[@name='PBCoreContributor::contributor']/f:data"/>
          </contributor>
          <xsl:for-each select="f:field[@name='PBCoreRole_Contributor::role']/f:data">
            <contributorRole>
              <xsl:if test="f:field[@name='PBCoreRole_Contributor::portrayal']/f:data">
                <xsl:attribute name="portrayal">
                  <xsl:value-of select="f:field[@name='PBCoreRole_Contributor::portrayal']/f:data"/>
                </xsl:attribute>
              </xsl:if>
              <xsl:value-of select="."/>
            </contributorRole>
          </xsl:for-each>
        </pbcoreContributor>
      </xsl:for-each>
      <xsl:for-each select="f:relatedset[@table='PBCorePublisher']/f:record">
        <pbcorePublisher>
          <publisher>
            <xsl:value-of select="f:field[@name='PBCorePublisher::publisher']/f:data"/>
          </publisher>
          <xsl:for-each select="f:field[@name='PBCoreRole_Publisher::role']/f:data">
            <publisherRole>
              <xsl:value-of select="."/>
            </publisherRole>
          </xsl:for-each>
        </pbcorePublisher>
      </xsl:for-each>
    </pbcoreDescriptionDocument>
  </xsl:template>
</xsl:stylesheet>
